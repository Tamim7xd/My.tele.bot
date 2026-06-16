"""
لوحة التحكم - نظام الحماية (protection).

يحتوي على:
- 🛡️ الحماية: تبديل كل ميزة (✅/❌) + الكلمات المحظورة + لوحة المحذوفات
- 📝 الكلمات المحظورة: عرض + 🗑️ حذف + ➕ إضافة (نمط rewards)
- 🗑️ لوحة المحذوفات: قائمة الأعضاء -> 5 محذوفات لكل صفحة -> ⚠️ تحذير / 🔇 كتم
- من صفحة العضو (👥 الأعضاء): 🛡️ استثناءات الحماية الفردية

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.members import queries as members_queries
from systems.moderation import queries as moderation_queries
from systems.protection import queries as protection_queries
from systems.protection import keyboards as prot_keyboards
from systems.protection.notifications import messages


router = Router(name="owner_protection")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== الإعدادات العامة =====

@router.callback_query(F.data == "owner:protection")
async def show_settings(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_toggle:"))
async def toggle_feature(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    feature_key = callback.data.split(":")[-1]

    pool = await get_pool()
    await protection_queries.toggle_feature(pool, feature_key)

    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== الكلمات المحظورة =====

@router.callback_query(F.data.startswith("owner:prot_words:"))
async def show_banned_words(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    words = settings.get("banned_words", [])

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_word_remove:"))
async def remove_banned_word(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    word = callback.data.split(":", 2)[-1]

    pool = await get_pool()
    words = await protection_queries.remove_banned_word(pool, word)

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.word_removed_text(word))


@router.callback_query(F.data == "owner:prot_word_add")
async def add_banned_word_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_protection_word)

    await callback.message.edit_text(
        messages.ADD_WORD_PROMPT,
        reply_markup=prot_keyboards.cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_protection_word)
async def add_banned_word_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    word = message.text.strip()

    if not word:
        return

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    existing_words = settings.get("banned_words", [])

    if word in existing_words:
        await message.reply(
            messages.ADD_WORD_DUPLICATE,
            reply_markup=prot_keyboards.cancel_keyboard(),
        )
        return

    words = await protection_queries.add_banned_word(pool, word)
    await state.clear()

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await message.reply(messages.word_added_text(word), reply_markup=keyboard)


# ===== لوحة المحذوفات =====

@router.callback_query(F.data == "owner:prot_deleted")
async def show_deleted_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    violators_count = await protection_queries.get_violators_with_logs_count(pool)

    text = messages.deleted_main_text(violators_count)
    keyboard = prot_keyboards.deleted_main_keyboard(violators_count)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_list:"))
async def show_deleted_list(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    pool = await get_pool()
    total = await protection_queries.get_violators_with_logs_count(pool)
    violators = await protection_queries.get_violators_with_logs_list(pool, offset=offset, limit=6)

    members_data = [(v["user_id"], v["username"], v["full_name"], v["deleted_count"]) for v in violators]

    text = messages.deleted_list_text(total)
    keyboard = prot_keyboards.deleted_list_keyboard(members_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_member:"))
async def show_member_deleted(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, page_str = callback.data.split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    await _render_member_deleted(callback, user_id, page)


async def _render_member_deleted(callback: CallbackQuery, user_id: int, page: int) -> None:
    pool = await get_pool()

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    total = await protection_queries.get_member_deleted_count(pool, user_id)
    entries = await protection_queries.get_member_deleted_entries(pool, user_id, offset=page * 5, limit=5)

    text = messages.member_deleted_text(member["full_name"], entries, total)
    keyboard = prot_keyboards.member_deleted_keyboard(user_id, page, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== إجراءات من لوحة المحذوفات: تحذير/كتم =====

@router.callback_query(F.data.startswith("owner:prot_del_warn:"))
async def deleted_warn(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, page_str = callback.data.split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    await moderation_queries.log_archive_entry(
        pool, user_id=user_id, action_type="warn", reason=None, replied_message=None, done_by=callback.from_user.id,
    )

    from systems.members.members import GROUP_ID_KEY
    from systems.moderation.notifications import messages as moderation_messages

    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            await callback.bot.send_message(
                chat_id=group_id,
                text=moderation_messages.warn_notification(
                    member["full_name"], member["username"], None, "المالك",
                ),
            )
        except Exception:
            pass

    await callback.answer(messages.WARN_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


@router.callback_query(F.data.startswith("owner:prot_del_mute:"))
async def deleted_mute(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, page_str = callback.data.split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    pool = await get_pool()

    until = moderation_queries.duration_to_datetime(10 * 60)  # 10 دقائق
    await moderation_queries.set_mute(pool, user_id, until)

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            from aiogram.types import ChatPermissions
            await callback.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
        except Exception:
            pass

    await callback.answer(messages.MUTE_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


# ===== استثناءات فردية لعضو =====

@router.callback_query(F.data.startswith("owner:prot_exc:"))
async def show_member_exceptions(callback: CallbackQuery) -> None:
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

    exceptions = await protection_queries.get_member_exceptions(pool, user_id)

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_exc_toggle:"))
async def toggle_member_exception(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, feature_key = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    await protection_queries.toggle_member_exception(pool, user_id, feature_key)

    member = await members_queries.get_member(pool, user_id)
    exceptions = await protection_queries.get_member_exceptions(pool, user_id)

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "owner:prot_reset")
async def reset_settings(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    from systems.protection.queries import DEFAULT_SETTINGS
    await protection_queries.set_protection_settings(pool, dict(DEFAULT_SETTINGS))

    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("✅ تم إعادة التعيين للإعدادات الافتراضية", show_alert=True)
