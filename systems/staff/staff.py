"""
نظام staff - لوحتا "مشرف" و"ادمن".

كلمتا التشغيل: "مشرف" و "ادمن" (بدون "/")
- "مشرف": يفتحها من رتبته moderator أو admin أو owner
- "ادمن": يفتحها من رتبته admin أو owner فقط

أي عضو آخر يكتب "مشرف"/"ادمن" -> صمت تام (لا رد).

كل لوحة تعرض:
- 🔴 عدد المخالفين (زر غير قابل للضغط)
- 📋 قائمة المخالفين (5 لكل صفحة)
        ↓ عند اختيار عضو
- 🔊 فتح الكتم (إن كان مكتوماً)
- ⏳ تمديد الكتم (فئة مدة -> مدة)
- ⬇️ تخفيض التحذيرات
- ✅ إلغاء الحظر (فقط في لوحة "ادمن"، إن كان محظوراً)

هذا الملف مستقل - يستخدم moderators/permissions و staff/queries و
moderation/queries (لرفع/تمديد الكتم).
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatPermissions

from core.database import get_pool, get_setting
from systems.moderators import permissions
from systems.members import queries as members_queries
from systems.moderation import queries as moderation_queries
from systems.moderation.notifications.messages import duration_label
from systems.staff import keyboards, queries as staff_queries
from systems.staff.notifications import messages


router = Router(name="staff")


MOD_TRIGGER = "مشرف"
ADMIN_TRIGGER = "ادمن"


# ===== فتح اللوحة =====

@router.message(F.text == MOD_TRIGGER)
async def open_mod_panel(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()

    if not await permissions.is_staff(pool, message.from_user.id):
        return  # صمت تام

    await _show_main_menu(message, pool)


@router.message(F.text == ADMIN_TRIGGER)
async def open_admin_panel(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()
    rank = await permissions.get_user_rank(pool, message.from_user.id)

    if rank not in ("admin", "owner"):
        return  # صمت تام

    await _show_main_menu(message, pool)


async def _show_main_menu(message: Message, pool) -> None:
    violators_count = await staff_queries.get_violators_count(pool)

    text = messages.main_menu_text(violators_count)
    keyboard = keyboards.main_menu_keyboard(violators_count)

    await message.answer(text, reply_markup=keyboard)


# ===== عناصر مشتركة =====

@router.callback_query(F.data == "staff:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "staff:close")
async def close_panel(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()


async def _is_authorized(pool, user_id: int, is_admin: bool) -> bool:
    """يتحقق أن المستخدم لا يزال يملك الصلاحية المناسبة (مشرف أو أدمن)."""
    if is_admin:
        rank = await permissions.get_user_rank(pool, user_id)
        return rank in ("admin", "owner")

    return await permissions.is_staff(pool, user_id)


# ===== قائمة المخالفين =====

@router.callback_query(F.data.startswith("staff:list:"))
async def show_violators_list(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    pool = await get_pool()

    if not await permissions.is_staff(pool, callback.from_user.id):
        await callback.answer()
        return

    rank = await permissions.get_user_rank(pool, callback.from_user.id)
    is_admin = rank in ("admin", "owner")

    total = await staff_queries.get_violators_count(pool)
    violators = await staff_queries.get_violators_list(pool, offset=offset, limit=5)

    violators_data = [(v["user_id"], v["username"], v["full_name"]) for v in violators]

    text = messages.violators_list_text(total)
    keyboard = keyboards.violators_list_keyboard(is_admin, violators_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== صفحة عضو (مشرف أو أدمن) =====

@router.callback_query(F.data.startswith("staff:mod:member:") | F.data.startswith("staff:admin:member:"))
async def show_member_page(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    await _render_member_page(callback, pool, is_admin, user_id, offset)


async def _render_member_page(callback: CallbackQuery, pool, is_admin: bool, user_id: int, offset: int) -> None:
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    violations_count = await members_queries.get_violations_count(pool, user_id)
    warnings_count = await members_queries.get_warnings_count(pool, user_id)

    text = messages.member_page_text(
        full_name=member["full_name"],
        username=member["username"],
        violations_count=violations_count,
        warnings_count=warnings_count,
        is_muted=member["is_muted"],
        is_banned=member["is_banned"],
    )

    keyboard = keyboards.member_page_keyboard(
        is_admin, user_id, offset, member["is_muted"], member["is_banned"]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== فتح الكتم =====

@router.callback_query(F.data.startswith("staff:mod:unmute:") | F.data.startswith("staff:admin:unmute:"))
async def unmute_member(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    if not member["is_muted"]:
        await callback.answer(messages.NOT_MUTED, show_alert=True)
        return

    await moderation_queries.unmute(pool, user_id)

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True, can_send_audios=True, can_send_documents=True,
                    can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                    can_send_voice_notes=True, can_send_polls=True,
                    can_send_other_messages=True, can_add_web_page_previews=True,
                ),
            )
        except Exception:
            pass

        try:
            await callback.bot.send_message(
                chat_id=group_id,
                text=f"🔊 تم رفع الكتم عن {member['full_name']}",
            )
        except Exception:
            pass

    await callback.answer(messages.UNMUTE_SUCCESS, show_alert=True)
    await _render_member_page(callback, pool, is_admin, user_id, offset)


# ===== تمديد الكتم =====

@router.callback_query(F.data.startswith("staff:mod:extend:") | F.data.startswith("staff:admin:extend:"))
async def extend_mute_start(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.extend_mute_category_text(member["full_name"])
    keyboard = keyboards.extend_category_keyboard(is_admin, user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("staff:mod:ext_cat:") | F.data.startswith("staff:admin:ext_cat:"))
async def extend_mute_category(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])
    category = parts[5]

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.extend_mute_list_text(member["full_name"])
    keyboard = keyboards.extend_duration_keyboard(is_admin, category, user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("staff:mod:ext_dur:") | F.data.startswith("staff:admin:ext_dur:"))
async def extend_mute_apply(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])
    seconds = int(parts[5])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    new_until = await staff_queries.extend_mute(pool, user_id, seconds)

    if new_until is None:
        await callback.answer()
        return

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=new_until,
            )
        except Exception:
            pass

        try:
            await callback.bot.send_message(
                chat_id=group_id,
                text=f"⏳ تم تمديد كتم {member['full_name']} بـ {duration_label(seconds)} إضافية.",
            )
        except Exception:
            pass

    duration_text = duration_label(seconds)

    await callback.answer(messages.extend_mute_success(member["full_name"], duration_text), show_alert=True)
    await _render_member_page(callback, pool, is_admin, user_id, offset)


# ===== إلغاء الحظر (أدمن فقط) =====

@router.callback_query(F.data.startswith("staff:admin:unban:"))
async def unban_member(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin=True):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    if not member["is_banned"]:
        await callback.answer(messages.NOT_BANNED, show_alert=True)
        return

    await moderation_queries.unban(pool, user_id)

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.unban_chat_member(chat_id=group_id, user_id=user_id, only_if_banned=True)
        except Exception:
            pass

        try:
            await callback.bot.send_message(
                chat_id=group_id,
                text=f"✅ تم رفع الحظر عن {member['full_name']}",
            )
        except Exception:
            pass

    await callback.answer(messages.UNBAN_SUCCESS, show_alert=True)
    await _render_member_page(callback, pool, True, user_id, offset)


# ===== تخفيض التحذيرات =====

@router.callback_query(F.data.startswith("staff:mod:reduce_warn:") | F.data.startswith("staff:admin:reduce_warn:"))
async def reduce_warning(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    is_admin = parts[1] == "admin"
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()

    if not await _is_authorized(pool, callback.from_user.id, is_admin):
        await callback.answer()
        return

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    success = await staff_queries.reduce_warning(pool, user_id)

    if not success:
        await callback.answer(messages.REDUCE_WARNING_NONE, show_alert=True)
        return

    new_count = await members_queries.get_warnings_count(pool, user_id)

    await callback.answer(messages.reduce_warning_success(member["full_name"], new_count), show_alert=True)
    await _render_member_page(callback, pool, is_admin, user_id, offset)
