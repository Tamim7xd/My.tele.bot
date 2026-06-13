"""
لوحة التحكم - الملف الرئيسي.

كلمة التشغيل: "admin" (إنجليزي فقط، بدون "/")
- في الخاص: المالك يكتب "admin" -> تفتح لوحة التحكم في الخاص
- في المجموعة: المالك يكتب "admin" -> تفتح لوحة التحكم داخل المجموعة

التعديلات التفاعلية الحالية:
- 💸 الخصم والمكافأة: تعديل القيم الأربعة (محفوظة في جدول settings)
- 🧹 التنظيف: تعديل عدد رسائل التنظيف (محفوظ في جدول settings)

كل نظام جديد يُبنى مستقبلاً يُضاف له:
1. زر في keyboards.py (main_menu_keyboard)
2. نص في notifications/messages.py
3. handler هنا لعرض/تعديل تفاصيله

بدون التأثير على الأنظمة الأخرى الموجودة في اللوحة.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool, set_setting
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.states import OwnerStates
from systems.owner.notifications import messages
from systems.moderators import queries as moderators_queries
from systems.wallet import wallet
from systems.rewards.keyboards import get_reward_amounts, REWARD_AMOUNTS_KEY
from systems.cleanup.cleanup import get_cleanup_range, CLEANUP_RANGE_KEY


router = Router(name="owner")


TRIGGER_WORD = "admin"


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


@router.message(F.text == TRIGGER_WORD)
async def open_panel(message: Message, state: FSMContext) -> None:
    """يفتح لوحة التحكم الرئيسية - المالك فقط، في الخاص أو المجموعة."""
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    await state.clear()
    await message.answer(messages.MAIN_MENU_TEXT, reply_markup=keyboards.main_menu_keyboard())


@router.callback_query(F.data == "owner:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(messages.MAIN_MENU_TEXT, reply_markup=keyboards.main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(messages.MAIN_MENU_TEXT, reply_markup=keyboards.main_menu_keyboard())
    await callback.answer()


# ===== الإداريين =====

@router.callback_query(F.data == "owner:moderators")
async def show_moderators(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()

    admin_count = await moderators_queries.get_staff_count(pool, "admin")
    moderator_count = await moderators_queries.get_staff_count(pool, "moderator")

    text = messages.moderators_text(admin_count, moderator_count)

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


# ===== الرصيد =====

@router.callback_query(F.data == "owner:wallet")
async def show_wallet(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()

    total_balance = await wallet.get_total_balance(pool)
    top_members = await wallet.get_top_balances(pool, limit=10)

    text = messages.wallet_text(total_balance, len(top_members))

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


# ===== الخصم والمكافأة =====

@router.callback_query(F.data == "owner:rewards")
async def show_rewards(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    amounts = await get_reward_amounts(pool)

    text = messages.rewards_text(amounts)

    await callback.message.edit_text(text, reply_markup=keyboards.rewards_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:rewards:edit")
async def edit_rewards_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_reward_amounts)

    await callback.message.edit_text(
        messages.REWARDS_EDIT_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_reward_amounts)
async def receive_reward_amounts(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    parts = [p.strip() for p in message.text.split(",")]

    if len(parts) != 4 or not all(p.isdigit() and int(p) > 0 for p in parts):
        await message.reply(
            messages.REWARDS_EDIT_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    amounts = [int(p) for p in parts]

    pool = await get_pool()
    await set_setting(pool, REWARD_AMOUNTS_KEY, amounts)

    await state.clear()

    await message.reply(
        messages.rewards_updated_text(amounts),
        reply_markup=keyboards.back_keyboard(),
    )


# ===== التنظيف =====

@router.callback_query(F.data == "owner:cleanup")
async def show_cleanup(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    cleanup_range = await get_cleanup_range(pool)

    text = messages.cleanup_text(cleanup_range)

    await callback.message.edit_text(text, reply_markup=keyboards.cleanup_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:cleanup:edit")
async def edit_cleanup_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_cleanup_range)

    await callback.message.edit_text(
        messages.CLEANUP_EDIT_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_cleanup_range)
async def receive_cleanup_range(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None or not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.reply(
            messages.CLEANUP_EDIT_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    new_range = int(message.text.strip())

    pool = await get_pool()
    await set_setting(pool, CLEANUP_RANGE_KEY, new_range)

    await state.clear()

    await message.reply(
        messages.cleanup_updated_text(new_range),
        reply_markup=keyboards.back_keyboard(),
    )
