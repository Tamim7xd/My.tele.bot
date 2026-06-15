"""
لوحة التحكم - نظام الإعلانات (announcements).

يحتوي على:
- 📢 الإعلانات: قائمة الإعلانات + ➕ إضافة
- صفحة إعلان: تعديل النص / تعديل مدة الحذف / حذف الإعلان
- إضافة إعلان (FSM): أمر التشغيل -> النص (أو تخطي) -> مدة الحذف -> حفظ

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.

ملاحظة: الملف/الملصق والزر الاختياري مؤجلان لمرحلة لاحقة (تم الاتفاق
على بناء الأساس أولاً: نص + مدة حذف + أمر تشغيل ديناميكي).
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.announcements import queries as announcements_queries
from systems.announcements import keyboards as ann_keyboards
from systems.announcements.notifications import messages


router = Router(name="owner_announcements")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== قائمة الإعلانات =====

@router.callback_query(F.data == "owner:announcements")
async def show_announcements_list(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    announcements = await announcements_queries.get_all_announcements(pool)

    text = messages.list_text(announcements)
    keyboard = ann_keyboards.list_keyboard(announcements)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== عرض/تعديل إعلان =====

@router.callback_query(F.data.startswith("owner:ann_view:"))
async def show_announcement(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    announcements = await announcements_queries.get_all_announcements(pool)

    if not (0 <= index < len(announcements)):
        await callback.answer()
        return

    ann = announcements[index]

    text = messages.announcement_details_text(ann)
    keyboard = ann_keyboards.announcement_details_keyboard(index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== حذف إعلان =====

@router.callback_query(F.data.startswith("owner:ann_delete:"))
async def delete_announcement_confirm(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await callback.message.edit_text(
        messages.DELETE_CONFIRM_TEXT,
        reply_markup=ann_keyboards.delete_confirm_keyboard(index),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("owner:ann_delete_confirm:"))
async def delete_announcement_apply(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    pool = await get_pool()
    await announcements_queries.delete_announcement(pool, index)

    announcements = await announcements_queries.get_all_announcements(pool)

    text = messages.list_text(announcements)
    keyboard = ann_keyboards.list_keyboard(announcements)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.DELETE_SUCCESS)


# ===== تعديل النص =====

@router.callback_query(F.data.startswith("owner:ann_edit_text:"))
async def edit_text_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await state.set_state(OwnerStates.waiting_announcement_edit_text)
    await state.update_data(ann_index=index)

    await callback.message.edit_text(
        messages.EDIT_TEXT_PROMPT,
        reply_markup=ann_keyboards.cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_edit_text)
async def edit_text_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    data = await state.get_data()
    index = data.get("ann_index")

    if index is None:
        await state.clear()
        return

    pool = await get_pool()
    announcements = await announcements_queries.get_all_announcements(pool)

    if not (0 <= index < len(announcements)):
        await state.clear()
        return

    new_text = "" if message.text.strip() == messages.SKIP_WORD else message.text

    ann = announcements[index]
    ann["text"] = new_text

    await announcements_queries.update_announcement(pool, index, ann)
    await state.clear()

    await message.reply(
        messages.edit_success_text(ann),
        reply_markup=ann_keyboards.announcement_details_keyboard(index),
    )


# ===== تعديل مدة الحذف =====

@router.callback_query(F.data.startswith("owner:ann_edit_delete:"))
async def edit_delete_after_prompt(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await callback.message.edit_text(
        messages.DELETE_AFTER_PROMPT,
        reply_markup=ann_keyboards.delete_after_keyboard(index),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("owner:ann_set_delete:"))
async def set_delete_after(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, target, seconds_str = callback.data.split(":")
    seconds = int(seconds_str)

    pool = await get_pool()

    if target == "new":
        # أثناء الإضافة - نأخذ القيم المخزنة في FSM ونحفظ الإعلان الجديد
        data = await state.get_data()

        ann = {
            "trigger": data.get("new_trigger"),
            "text": data.get("new_text", ""),
            "file_id": None,
            "file_type": None,
            "delete_after": seconds,
            "button_text": None,
            "button_url": None,
        }

        if ann["trigger"] is None:
            await state.clear()
            await callback.answer()
            return

        await announcements_queries.add_announcement(pool, ann)
        await state.clear()

        announcements = await announcements_queries.get_all_announcements(pool)
        index = len(announcements) - 1

        await callback.message.edit_text(
            messages.add_success_text(ann),
            reply_markup=ann_keyboards.announcement_details_keyboard(index),
        )
        await callback.answer()
        return

    # تعديل إعلان موجود
    index = int(target)
    announcements = await announcements_queries.get_all_announcements(pool)

    if not (0 <= index < len(announcements)):
        await callback.answer()
        return

    ann = announcements[index]
    ann["delete_after"] = seconds

    await announcements_queries.update_announcement(pool, index, ann)

    await callback.message.edit_text(
        messages.delete_after_updated_text(ann),
        reply_markup=ann_keyboards.announcement_details_keyboard(index),
    )
    await callback.answer()


# ===== إضافة إعلان جديد (FSM) =====

@router.callback_query(F.data == "owner:ann_add")
async def add_announcement_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_announcement_trigger)

    await callback.message.edit_text(
        messages.ADD_TRIGGER_PROMPT,
        reply_markup=ann_keyboards.cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_trigger)
async def add_announcement_trigger_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    trigger = message.text.strip()

    if " " in trigger or trigger.startswith("/") or len(trigger) == 0 or len(trigger) > 30:
        await message.reply(
            messages.ADD_TRIGGER_INVALID,
            reply_markup=ann_keyboards.cancel_keyboard(),
        )
        return

    pool = await get_pool()

    if await announcements_queries.trigger_exists(pool, trigger):
        await message.reply(
            messages.ADD_TRIGGER_DUPLICATE,
            reply_markup=ann_keyboards.cancel_keyboard(),
        )
        return

    await state.update_data(new_trigger=trigger)
    await state.set_state(OwnerStates.waiting_announcement_text)

    await message.reply(
        messages.ADD_TEXT_PROMPT,
        reply_markup=ann_keyboards.cancel_keyboard(),
    )


@router.message(OwnerStates.waiting_announcement_text)
async def add_announcement_text_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    new_text = "" if message.text.strip() == messages.SKIP_WORD else message.text

    await state.update_data(new_text=new_text)

    await message.reply(
        messages.DELETE_AFTER_PROMPT,
        reply_markup=ann_keyboards.delete_after_keyboard(index=None),
    )
