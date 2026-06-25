"""
نظام التفاعل التلقائي (engagement) - النسخة المتطورة.

- رسالة دورية في المجموعة بزر يفتح قائمة الخاص
- قائمة الخاص: أزرار اختيارية (عضوية/ألقاب/سوق/ترتيب/إدارة) حسب الرتبة
- إمكانية إيقاف الأوامر النصية بالمجموعة (سوق/عضوية/لقب/مشرف/ادمن/admin)
  وتوجيه العضو لاستخدام القائمة في الخاص بدلاً منها
"""

import asyncio

from aiogram import Router, F, Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank
from systems.engagement.notifications import messages


router = Router(name="engagement")

# الأوامر النصية التي يمكن إيقافها بالمجموعة
DISABLED_GROUP_COMMANDS = {
    "سوق", "متجر", "شراء",
    "عضوية", "عضويتي",
    "لقب", "القاب", "مشتريات", "مشترياتي",
    "مشرف", "ادمن", "admin",
}


def _build_member_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """يبني لوحة مفاتيح العضو العادي حسب الأزرار المفعّلة."""
    buttons = []
    row = []

    if settings.get("btn_account", True):
        row.append(InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"))

    if settings.get("btn_membership", True):
        row.append(InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_titles", True):
        row.append(InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"))

    if settings.get("btn_shop", True):
        row.append(InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_leaderboard", True):
        buttons.append([InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def _build_staff_keyboard(settings: dict, rank: str) -> InlineKeyboardMarkup:
    """يبني لوحة مفاتيح المشرف/الأدمن مع زر اللوحة الإدارية."""
    buttons = []
    row = []

    if settings.get("btn_account", True):
        row.append(InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"))

    if settings.get("btn_membership", True):
        row.append(InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_titles", True):
        row.append(InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"))

    if settings.get("btn_shop", True):
        row.append(InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_leaderboard", True):
        buttons.append([InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")])

    if settings.get("btn_staff_panel", True):
        if rank == "admin":
            label, cmd = "👮 لوحة الأدمن", "ادمن"
        else:
            label, cmd = "🛡️ لوحة المشرف", "مشرف"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"eng:cmd:{cmd}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def _build_owner_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """يبني لوحة مفاتيح المالك مع زر لوحة التحكم الكاملة."""
    buttons = []
    row = []

    if settings.get("btn_account", True):
        row.append(InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"))

    if settings.get("btn_membership", True):
        row.append(InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_titles", True):
        row.append(InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"))

    if settings.get("btn_shop", True):
        row.append(InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق"))

    if row:
        buttons.append(row)
        row = []

    if settings.get("btn_leaderboard", True):
        buttons.append([InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")])

    if settings.get("btn_staff_panel", True):
        buttons.append([InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="eng:cmd:admin")])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


# ===== معالج إيقاف الأوامر النصية بالمجموعة =====

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def intercept_disabled_commands(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise SkipHandler

    text = message.text.strip()

    if text not in DISABLED_GROUP_COMMANDS:
        raise SkipHandler

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    if not settings.get("disable_group_commands", False):
        raise SkipHandler

    # الأمر موقوف — أرشد العضو للخاص
    await message.reply(
        "💬 هذا الأمر متاح عبر قائمتك الشخصية فقط.\nاضغط الزر في رسالة القائمة لفتحها في الخاص.",
    )


# ===== معالج الزر في المجموعة =====

@router.callback_query(F.data == "eng:open_menu")
async def open_personal_menu(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    full_name = callback.from_user.full_name

    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)
    settings = await engagement_queries.get_engagement_settings(pool)

    if user_id == OWNER_ID:
        text = messages.member_menu_text(full_name)
        keyboard = _build_owner_keyboard(settings)
    elif rank in ("admin", "moderator"):
        text = messages.staff_menu_text(full_name, rank)
        keyboard = _build_staff_keyboard(settings, rank)
    else:
        text = messages.member_menu_text(full_name)
        keyboard = _build_member_keyboard(settings)

    if keyboard is None:
        await callback.answer("لا توجد أزرار مفعّلة حالياً.")
        return

    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
        )
        await callback.answer(messages.MENU_OPENED)
    except Exception:
        await callback.answer(messages.NEED_START, show_alert=True)


# ===== تنفيذ الأوامر من الخاص =====

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    cmd = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

    if cmd in ("مشرف", "ادمن", "admin"):
        if user_id != OWNER_ID and rank not in ("admin", "moderator"):
            await callback.answer()
            return

    await callback.answer()

    if cmd == "حساب":
        from systems.members import queries as members_queries
        from systems.members.notifications import messages as member_messages

        member = await members_queries.get_member(pool, user_id)

        if member is None:
            await callback.message.answer("❌ لم يتم تسجيلك بعد. أرسل رسالة في المجموعة أولاً.")
            return

        warnings_count = await members_queries.get_warnings_count(pool, user_id)
        violations_count = await members_queries.get_violations_count(pool, user_id)

        active_title_name = None
        membership_name = None

        try:
            from systems.shop import queries as shop_queries
            from systems.shop import member_queries as shop_member_queries

            active_title_id = await shop_member_queries.get_active_title(pool, user_id)
            if active_title_id:
                title = await shop_queries.get_title_by_id(pool, active_title_id)
                if title:
                    active_title_name = title["name"]

            membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
            if membership_status:
                membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
                if membership:
                    membership_name = membership["name"]
        except Exception:
            pass

        text = member_messages.account_card_text(
            full_name=member["full_name"],
            username=member["username"],
            level=member["level"],
            messages_count=member["messages_count"],
            balance=member["balance"],
            warnings_count=warnings_count,
            violations_count=violations_count,
            games_played=member["games_played"],
            games_won=member["games_won"],
            active_title_name=active_title_name,
            membership_name=membership_name,
        )
        await callback.message.answer(text)

    elif cmd == "عضوية":
        from systems.shop import queries as shop_queries
        from systems.shop import member_queries as shop_member_queries
        from systems.shop.notifications import messages as shop_messages

        status = await shop_member_queries.get_member_membership_status(pool, user_id)

        if status is None:
            await callback.message.answer(shop_messages.my_membership_text(None, None))
        else:
            membership = await shop_queries.get_membership_by_id(pool, status["membership_id"])
            expires_str = status["expires_at"].strftime("%Y-%m-%d %H:%M") if status["expires_at"] else "بلا انتهاء"
            await callback.message.answer(shop_messages.my_membership_text(membership, expires_str))

    elif cmd == "لقب":
        from systems.shop import queries as shop_queries
        from systems.shop import member_queries as shop_member_queries
        from systems.shop.notifications import messages as shop_messages
        from systems.shop import keyboards as shop_keyboards

        owned_title_ids = await shop_member_queries.get_owned_titles(pool, user_id)
        all_titles = await shop_queries.get_titles(pool)
        owned_titles = [t for t in all_titles if t["id"] in owned_title_ids]
        active_title_id = await shop_member_queries.get_active_title(pool, user_id)

        text = shop_messages.my_titles_text(owned_titles, active_title_id)
        keyboard = shop_keyboards.my_titles_keyboard(owned_titles) if owned_titles else None

        await callback.message.answer(text, reply_markup=keyboard)

    elif cmd == "سوق":
        from systems.shop import keyboards as shop_keyboards
        from systems.shop.notifications import messages as shop_messages

        keyboard = shop_keyboards.main_menu_keyboard(user_id)
        await callback.message.answer(shop_messages.MAIN_MENU_TEXT, reply_markup=keyboard)

    elif cmd == "ترتيب":
        from systems.wallet import wallet as wallet_module
        top = await wallet_module.get_top_balances(pool, limit=3)

        if not top:
            await callback.message.answer("🏆 لا يوجد أعضاء مسجلون بعد.")
            return

        lines = ["🏆 <b>قائمة الترتيب</b>", "━━━━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉"]

        for i, member in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            name = member["full_name"]
            balance = member["balance"]
            lines.append(f"{medal} {name}: {balance:,} د.ع")

        await callback.message.answer("\n".join(lines))

    elif cmd in ("مشرف", "ادمن", "admin"):
        cmd_map = {"مشرف": "مشرف", "ادمن": "ادمن", "admin": "admin"}
        await callback.message.answer(
            f"💬 اكتب «{cmd_map.get(cmd, cmd)}» في المجموعة لفتح لوحتك."
        )


# ===== مجدول الإرسال الدوري =====

async def engagement_scheduler_loop(bot: Bot) -> None:
    while True:
        try:
            await _send_engagement_message(bot)
        except Exception:
            pass

        pool = await get_pool()
        settings = await engagement_queries.get_engagement_settings(pool)
        interval = settings.get("interval_seconds", 3600)

        await asyncio.sleep(max(interval, 30))


async def _send_engagement_message(bot: Bot) -> None:
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    if not settings.get("enabled", False):
        return

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if not group_id:
        return

    text = settings.get("message_text", "👋 اضغط الزر لفتح قائمتك!")
    button_text = settings.get("button_text", "📋 قائمتي")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="eng:open_menu")]
        ]
    )

    try:
        await bot.send_message(chat_id=group_id, text=text, reply_markup=keyboard)
    except Exception:
        pass
