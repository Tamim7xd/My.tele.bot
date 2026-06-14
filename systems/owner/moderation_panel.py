"""
لوحة التحكم - أزرار moderation (كتم/حظر/تحذير) من صفحة العضو.

يحتوي على:
- 🔇 كتم / 🚫 حظر: فئة المدة -> مدة محددة -> تطبيق فوري
- 🔊 رفع الكتم / ✅ رفع الحظر: تطبيق فوري
- ⚠️ تحذير: تأكيد -> تطبيق فوري

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
يستخدم نفس قواعد moderation (queries, duration_to_datetime, إشعارات المجموعة).
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, ChatPermissions

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.notifications import messages
from systems.members import queries as members_queries
from systems.moderation import queries as moderation_queries
from systems.moderation.notifications import messages as moderation_messages
from systems.members.members import GROUP_ID_KEY


router = Router(name="owner_moderation")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


async def _refresh_member_page(callback: CallbackQuery, user_id: int, offset: int) -> None:
    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.member_page_text(
        full_name=member["full_name"],
        username=member["username"],
        rank=member["rank"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        is_muted=member["is_muted"],
        is_banned=member["is_banned"],
    )

    keyboard = keyboards.member_page_keyboard(
        user_id, offset, member["rank"],
        is_muted=member["is_muted"], is_banned=member["is_banned"],
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ===== فتح اختيار فئة المدة للكتم/الحظر =====

@router.callback_query(F.data.startswith("owner:member_mute:"))
async def member_mute_start(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.member_mute_category_text(member["full_name"])
    keyboard = keyboards.member_mute_ban_duration_keyboard("mute", user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:member_ban:"))
async def member_ban_start(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.member_ban_category_text(member["full_name"])
    keyboard = keyboards.member_mute_ban_duration_keyboard("ban", user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== اختيار فئة المدة =====

@router.callback_query(F.data.startswith("owner:mb_cat:"))
async def member_mute_ban_category(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, action, user_id_str, offset_str, category = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    action_label = "كتم" if action == "mute" else "حظر"
    text = messages.member_duration_list_text(member["full_name"], action_label)
    keyboard = keyboards.member_mute_ban_duration_list_keyboard(action, category, user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mb_action:"))
async def member_mute_ban_back(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, action, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    if action == "mute":
        text = messages.member_mute_category_text(member["full_name"])
    else:
        text = messages.member_ban_category_text(member["full_name"])

    keyboard = keyboards.member_mute_ban_duration_keyboard(action, user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== تطبيق الكتم/الحظر =====

@router.callback_query(F.data.startswith("owner:mb_dur:"))
async def apply_mute_ban(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, action, user_id_str, offset_str, seconds_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    seconds = int(seconds_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    until = moderation_queries.duration_to_datetime(seconds)
    duration_text = moderation_messages.duration_label(seconds)

    group_id = await get_setting(pool, GROUP_ID_KEY)

    if action == "mute":
        await moderation_queries.set_mute(pool, user_id, until)

        if group_id:
            try:
                await callback.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
            except Exception:
                pass

            try:
                await callback.bot.send_message(
                    chat_id=group_id,
                    text=moderation_messages.mute_notification(
                        member["full_name"], member["username"], duration_text, None, "المالك",
                    ),
                )
            except Exception:
                pass

        await moderation_queries.log_archive_entry(
            pool, user_id=user_id, action_type="mute", reason=None, replied_message=None, done_by=callback.from_user.id,
        )

        await callback.answer(messages.member_mute_applied_text(member["full_name"], duration_text), show_alert=True)

    else:  # ban
        await moderation_queries.set_ban(pool, user_id, until)

        if group_id:
            try:
                await callback.bot.ban_chat_member(chat_id=group_id, user_id=user_id, until_date=until)
            except Exception:
                pass

            try:
                await callback.bot.send_message(
                    chat_id=group_id,
                    text=moderation_messages.ban_notification(
                        member["full_name"], member["username"], duration_text, None, "المالك",
                    ),
                )
            except Exception:
                pass

        await moderation_queries.log_archive_entry(
            pool, user_id=user_id, action_type="ban", reason=None, replied_message=None, done_by=callback.from_user.id,
        )

        await callback.answer(messages.member_ban_applied_text(member["full_name"], duration_text), show_alert=True)

    await _refresh_member_page(callback, user_id, offset)


# ===== رفع الكتم/الحظر =====

@router.callback_query(F.data.startswith("owner:member_unmute:"))
async def member_unmute(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    await moderation_queries.unmute(pool, user_id)

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

    await callback.answer(messages.member_unmute_applied_text(member["full_name"]), show_alert=True)
    await _refresh_member_page(callback, user_id, offset)


@router.callback_query(F.data.startswith("owner:member_unban:"))
async def member_unban(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    await moderation_queries.unban(pool, user_id)

    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.unban_chat_member(chat_id=group_id, user_id=user_id, only_if_banned=True)
        except Exception:
            pass

    await callback.answer(messages.member_unban_applied_text(member["full_name"]), show_alert=True)
    await _refresh_member_page(callback, user_id, offset)


# ===== التحذير =====

@router.callback_query(F.data.startswith("owner:member_warn:"))
async def member_warn_prompt(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.member_warn_confirm_text(member["full_name"])
    keyboard = keyboards.member_warn_confirm_keyboard(user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mb_warn_confirm:"))
async def member_warn_confirm(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    await moderation_queries.log_archive_entry(
        pool, user_id=user_id, action_type="warn", reason=None, replied_message=None, done_by=callback.from_user.id,
    )

    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.send_message(
                chat_id=group_id,
                text=moderation_messages.warn_notification(member["full_name"], member["username"], None, "المالك"),
            )
        except Exception:
            pass

    await callback.answer(messages.member_warn_applied_text(member["full_name"]), show_alert=True)
    await _refresh_member_page(callback, user_id, offset)
