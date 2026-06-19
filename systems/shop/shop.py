"""
نظام المتجر (shop) - الملف الرئيسي الكامل والمعدل.

أوامر التشغيل: "سوق"، "متجر"، "شراء" -> يفتح المتجر، حصرية لمن كتبها.
أمر "مسح"/"مسح محادثتي"/"مسح محادثاته" -> مجاني وفوري لأصحاب العضويات ويحذف رسائلهم فقط.
أمر "عضوية"/"عضويتي" -> تفاصيل العضوية الحالية.
أمر "لقب"/"القاب"/"مشتريات"/"مشترياتي" -> الألقاب المملوكة + تفعيل أحدها.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.shop import queries as shop_queries
from systems.shop import member_queries as shop_member_queries
from systems.shop import keyboards as shop_keyboards
from systems.shop.notifications import messages


router = Router(name="shop")


SHOP_TRIGGERS = {"سوق", "متجر", "شراء"}
CLEAR_TRIGGERS = {"مسح", "مسح محادثتي", "مسح محادثاته"}
MEMBERSHIP_TRIGGERS = {"عضوية", "عضويتي"}
TITLES_TRIGGERS = {"لقب", "القاب", "مشتريات", "مشترياتي"}


def _is_owner_callback(callback: CallbackQuery, owner_id: int) -> bool:
    return callback.from_user is not None and callback.from_user.id == owner_id


# ===== فتح المتجر =====

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.in_(SHOP_TRIGGERS))
async def open_shop(message: Message) -> None:
    if message.from_user is None:
        return

    owner_id = message.from_user.id
    keyboard = shop_keyboards.main_menu_keyboard(owner_id)

    await message.reply(messages.MAIN_MENU_TEXT, reply_markup=keyboard)


@router.callback_query(F.data.startswith("shop:main:"))
async def back_to_main(callback: CallbackQuery) -> None:
    owner_id = int(callback.data.split(":")[-1])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    keyboard = shop_keyboards.main_menu_keyboard(owner_id)
    await callback.message.edit_text(messages.MAIN_MENU_TEXT, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("shop:close:"))
async def close_shop(callback: CallbackQuery) -> None:
    owner_id = int(callback.data.split(":")[-1])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data == "shop:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ===== مسح المحادثة من داخل قائمة المتجر (تظل مدفوعة بفلوس) =====

@router.callback_query(F.data.startswith("shop:clear_intro:"))
async def clear_intro(callback: CallbackQuery) -> None:
    owner_id = int(callback.data.split(":")[-1])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()
    price = await shop_queries.get_clear_chat_price(pool)

    keyboard = shop_keyboards.clear_chat_keyboard(owner_id)
    await callback.message.edit_text(messages.clear_chat_intro_text(price), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("shop:clear_confirm:"))
async def clear_confirm(callback: CallbackQuery) -> None:
    owner_id = int(callback.data.split(":")[-1])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=owner_id, username=callback.from_user.username, full_name=callback.from_user.full_name,
    )

    price = await shop_queries.get_clear_chat_price(pool)
    balance = await wallet.get_balance(pool, owner_id)

    if balance < price:
        await callback.answer(messages.INSUFFICIENT_BALANCE, show_alert=True)
        return

    await wallet.deduct_balance(pool, owner_id, price)

    deleted_count = await _delete_member_messages(callback, owner_id)

    await shop_member_queries.log_clear_chat(pool, owner_id, deleted_count)
    await shop_member_queries.set_last_clear_chat_at(pool, owner_id)

    await callback.message.edit_text(
        messages.clear_chat_done_text(deleted_count),
        reply_markup=shop_keyboards.back_to_main_keyboard(owner_id),
    )
    await callback.answer()


# ===== أمر "مسح" النصي المباشر (مجاني تماماً وفوري لأصحاب العضويات ويحذف رسائلهم فقط) =====

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.in_(CLEAR_TRIGGERS))
async def clear_chat_command(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()
    user_id = message.from_user.id

    membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)

    if membership_status is None:
        return  # صمت تام إذا لم تكن هناك عضوية نشطة

    membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])

    if membership is None or not membership.get("can_clear_chat"):
        return  # صمت تام إذا كانت العضوية لا تدعم ميزة المسح

    # التنفيذ المجاني والفوري للعضو
    deleted_count = await _delete_member_messages(message, user_id)

    await shop_member_queries.log_clear_chat(pool, user_id, deleted_count)
    await shop_member_queries.set_last_clear_chat_at(pool, user_id)

    # إشعار مؤقت للعضو ثم حذفه ليبقى الشات نظيفاً
    notice = await message.reply(messages.clear_chat_done_text(deleted_count))
    
    import asyncio
    await asyncio.sleep(3)
    try:
        await notice.delete()
    except Exception:
        pass


async def _delete_member_messages(callback: CallbackQuery | Message, user_id: int) -> int:
    """دالة فحص وحذف ذكية: تحذف فقط رسائل العضو المستهدف وتتخطى البقية تماماً."""
    pool = await get_pool()
    chat_id = callback.chat.id if isinstance(callback, Message) else callback.message.chat.id
    start_id = callback.message_id if isinstance(callback, Message) else callback.message.message_id
    
    range_count = await shop_queries.get_clear_chat_range(pool)
    end_id = max(1, start_id - range_count)

    deleted = 0

    for msg_id in range(start_id, end_id - 1, -1):
        try:
            # حذف رسالة الأمر النصي نفسها أولاً في حال كان الاستدعاء من رسالة مباشرة
            if isinstance(callback, Message) and msg_id == start_id:
                await callback.delete()
                deleted += 1
                continue
                
            bot_obj = callback.bot if isinstance(callback, Message) else callback.message.bot
            # تليجرام يحذف رسائل الشخص نفسه تلقائياً، وإذا كانت لآخرين ستفشل المحاولة ويتخطاها لضمان حماية رسائل الآخرين
            await bot_obj.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted += 1
        except Exception:
            continue

    return deleted


# ===== العضويات =====

@router.callback_query(F.data.startswith("shop:memberships:"))
async def show_memberships(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    owner_id = int(parts[2])
    index = int(parts[3])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()
    memberships = await shop_queries.get_memberships(pool)

    if not memberships or not (0 <= index < len(memberships)):
        await callback.answer()
        return

    text = messages.membership_details_text(memberships[index])
    keyboard = shop_keyboards.memberships_list_keyboard(owner_id, memberships, index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("shop:buy_membership:"))
async def buy_membership(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    owner_id = int(parts[2])
    membership_id = parts[3]

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=owner_id, username=callback.from_user.username, full_name=callback.from_user.full_name,
    )

    existing = await shop_member_queries.get_member_membership_status(pool, owner_id)

    if existing is not None:
        await callback.answer(messages.MEMBERSHIP_ALREADY_ACTIVE, show_alert=True)
        return

    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    balance = await wallet.get_balance(pool, owner_id)

    if balance < membership["price"]:
        await callback.answer(messages.INSUFFICIENT_BALANCE, show_alert=True)
        return

    await wallet.deduct_balance(pool, owner_id, membership["price"])

    expires_at = await shop_member_queries.set_member_membership(
        pool, owner_id, membership_id, membership["duration_seconds"]
    )

    await shop_member_queries.log_purchase(pool, owner_id, "membership", membership_id, membership["price"])

    expires_str = expires_at.strftime("%Y-%m-%d %H:%M") if expires_at else "بلا انتهاء (دائمة)"

    await callback.message.edit_text(
        messages.membership_purchased_text(membership["name"], expires_str),
        reply_markup=shop_keyboards.back_to_main_keyboard(owner_id),
    )
    await callback.answer()


# ===== الألقاب =====

@router.callback_query(F.data.startswith("shop:titles:"))
async def show_titles(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    owner_id = int(parts[2])
    index = int(parts[3])

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()
    titles = await shop_queries.get_titles(pool)

    if not titles or not (0 <= index < len(titles)):
        await callback.answer()
        return

    owned_titles = await shop_member_queries.get_owned_titles(pool, owner_id)
    already_owned = titles[index]["id"] in owned_titles

    text = messages.title_details_text(titles[index], already_owned)
    keyboard = shop_keyboards.titles_list_keyboard(owner_id, titles, index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("shop:buy_title:"))
async def buy_title(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    owner_id = int(parts[2])
    title_id = parts[3]

    if not _is_owner_callback(callback, owner_id):
        await callback.answer()
        return

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=owner_id, username=callback.from_user.username, full_name=callback.from_user.full_name,
    )

    owned_titles = await shop_member_queries.get_owned_titles(pool, owner_id)

    if title_id in owned_titles:
        await callback.answer(messages.TITLE_ALREADY_OWNED, show_alert=True)
        return

    title = await shop_queries.get_title_by_id(pool, title_id)

    if title is None:
        await callback.answer()
        return

    balance = await wallet.get_balance(pool, owner_id)

    if balance < title["price"]:
        await callback.answer(messages.INSUFFICIENT_BALANCE, show_alert=True)
        return

    await wallet.deduct_balance(pool, owner_id, title["price"])
    await shop_member_queries.add_owned_title(pool, owner_id, title_id)
    await shop_member_queries.log_purchase(pool, owner_id, "title", title_id, title["price"])

    await callback.message.edit_text(
        messages.title_purchased_text(title["name"]),
        reply_markup=shop_keyboards.back_to_main_keyboard(owner_id),
    )
    await callback.answer()


# ===== أمر "عضوية"/"عضويتي" =====

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.in_(MEMBERSHIP_TRIGGERS))
async def my_membership(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()
    user_id = message.from_user.id

    status = await shop_member_queries.get_member_membership_status(pool, user_id)

    if status is None:
        await message.reply(messages.my_membership_text(None, None))
        return

    membership = await shop_queries.get_membership_by_id(pool, status["membership_id"])

    if membership is None:
        await message.reply(messages.my_membership_text(None, None))
        return

    expires_str = status["expires_at"].strftime("%Y-%m-%d %H:%M") if status["expires_at"] else "بلا انتهاء (دائمة)"

    await message.reply(messages.my_membership_text(membership, expires_str))


# ===== أمر "لقب"/"القاب"/"مشتريات"/"مشترياتي" =====

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.in_(TITLES_TRIGGERS))
async def my_titles(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()
    user_id = message.from_user.id

    owned_title_ids = await shop_member_queries.get_owned_titles(pool, user_id)

    if not owned_title_ids:
        await message.reply(messages.my_titles_text([], None))
        return

    all_titles = await shop_queries.get_titles(pool)
    owned_titles = [t for t in all_titles if t["id"] in owned_title_ids]

    active_title_id = await shop_member_queries.get_active_title(pool, user_id)

    text = messages.my_titles_text(owned_titles, active_title_id)
    keyboard = shop_keyboards.my_titles_keyboard(owned_titles)

    await message.reply(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("shop:activate_title:"))
async def activate_title(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    title_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    pool = await get_pool()
    owned_title_ids = await shop_member_queries.get_owned_titles(pool, user_id)

    if title_id not in owned_title_ids:
        await callback.answer()
        return

    await shop_member_queries.set_active_title(pool, user_id, title_id)

    title = await shop_queries.get_title_by_id(pool, title_id)

    all_titles = await shop_queries.get_titles(pool)
    owned_titles = [t for t in all_titles if t["id"] in owned_title_ids]

    await callback.message.edit_text(
        messages.my_titles_text(owned_titles, title_id),
        reply_markup=shop_keyboards.my_titles_keyboard(owned_titles),
    )
    await callback.answer(messages.title_activated_text(title["name"]))
