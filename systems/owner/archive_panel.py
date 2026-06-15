"""
لوحة التحكم - نظام الأرشيف (archive).

يحتوي على:
- 📁 الأرشيف (من القائمة الرئيسية): قائمة أعضاء مستقلة (تصفح + بحث)
- 📁 الأرشيف (من صفحة عضو في 👥 الأعضاء)
- صفحة أرشيف العضو: 6 فئات بعداد كل واحدة + 📋 العدد الكامل
- صفحة فئة: تفاصيل كاملة (آخر 10) + 📋 نسخ (رسالة منفصلة قابلة للنسخ)
- صفحة العدد الكامل: ملخص شامل + 📋 نسخ

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner import keyboards as owner_keyboards
from systems.owner.states import OwnerStates
from systems.members import queries as members_queries
from systems.archive import queries as archive_queries
from systems.archive import keyboards as archive_keyboards
from systems.archive.notifications import messages


router = Router(name="owner_archive")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


def _escape_html(text: str) -> str:
    """يهرب رموز HTML الخاصة قبل وضع النص داخل <code>."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ===== قائمة الأرشيف المستقلة (من القائمة الرئيسية) =====

@router.callback_query(F.data.startswith("owner:archive_list:"))
async def show_archive_list(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    total = await members_queries.get_members_count(pool)
    members = await members_queries.get_all_members(pool, offset=offset, limit=6)

    members_data = [(m["user_id"], m["username"], m["full_name"]) for m in members]

    if total == 0:
        text = "📁 <b>الأرشيف</b>\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء مسجلين حتى الآن."
    else:
        text = f"📁 <b>الأرشيف</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً، أو استخدم 🔍 البحث:"

    keyboard = archive_keyboards.archive_list_keyboard(members_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== بحث في قائمة الأرشيف المستقلة =====

@router.callback_query(F.data == "owner:archive_search")
async def archive_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_archive_search)

    await callback.message.edit_text(
        "🔍 أرسل اسم أو يوزر العضو للبحث عنه.",
        reply_markup=owner_keyboards.search_cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_archive_search)
async def archive_search_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    pool = await get_pool()
    results = await members_queries.search_member(pool, message.text.strip())

    await state.clear()

    if not results:
        await message.reply(
            "❌ لم يتم العثور على أي عضو مطابق.",
            reply_markup=owner_keyboards.search_cancel_keyboard(),
        )
        return

    results_data = [(m["user_id"], m["username"], m["full_name"]) for m in results]

    await message.reply(
        "🔍 نتائج البحث:",
        reply_markup=archive_keyboards.archive_search_results_keyboard(results_data),
    )


# ===== صفحة أرشيف العضو =====

@router.callback_query(F.data.startswith("owner:archive_member:"))
async def show_archive_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])
    offset = int(parts[3])
    source = parts[4] if len(parts) > 4 else "list"

    await state.clear()

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    counts = await archive_queries.get_all_counts(pool, user_id)

    text = messages.archive_main_text(member["full_name"], counts)
    keyboard = archive_keyboards.archive_main_keyboard(user_id, offset, source)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== صفحة تفاصيل فئة =====

@router.callback_query(F.data.startswith("owner:arch_cat:"))
async def show_category_entries(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    action_type = parts[2]
    user_id = int(parts[3])
    offset = int(parts[4])
    source = parts[5] if len(parts) > 5 else "list"

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    total = await archive_queries.get_category_count(pool, user_id, action_type)
    entries = await archive_queries.get_category_entries(pool, user_id, action_type, offset=0, limit=10)

    text = messages.category_entries_text(member["full_name"], action_type, entries, total)
    keyboard = archive_keyboards.category_entries_keyboard(action_type, user_id, offset, source)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:arch_copy:"))
async def copy_category_entries(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    action_type = parts[2]
    user_id = int(parts[3])
    offset = int(parts[4])

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    total = await archive_queries.get_category_count(pool, user_id, action_type)
    entries = await archive_queries.get_category_entries(pool, user_id, action_type, offset=0, limit=10)

    copy_text = messages.category_copy_text(member["full_name"], action_type, entries, total)

    await callback.message.answer(f"<code>{_escape_html(copy_text)}</code>")
    await callback.answer(messages.COPY_SENT)


# ===== صفحة العدد الكامل =====

@router.callback_query(F.data.startswith("owner:arch_summary:"))
async def show_full_summary(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])
    offset = int(parts[3])
    source = parts[4] if len(parts) > 4 else "list"

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    counts = await archive_queries.get_all_counts(pool, user_id)

    text = messages.full_summary_text(member["full_name"], counts)
    keyboard = archive_keyboards.full_summary_keyboard(user_id, offset, source)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:arch_summary_copy:"))
async def copy_full_summary(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    counts = await archive_queries.get_all_counts(pool, user_id)
    all_entries = await archive_queries.get_all_entries(pool, user_id, limit_per_category=10)

    copy_text = messages.full_summary_copy_text(member["full_name"], all_entries, counts)

    await callback.message.answer(f"<code>{_escape_html(copy_text)}</code>")
    await callback.answer(messages.COPY_SENT)
