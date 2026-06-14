"""
لوحة التحكم - الملف الرئيسي.

كلمة التشغيل: "admin" (إنجليزي فقط، بدون "/")
- في الخاص: المالك يكتب "admin" -> تفتح لوحة التحكم في الخاص
- في المجموعة: المالك يكتب "admin" -> تفتح لوحة التحكم داخل المجموعة

يحتوي هذا الملف على:
- فتح اللوحة الرئيسية + الرجوع + الإلغاء
- 💰 الرصيد (ملخص عام)
- 💸 الخصم والمكافأة (قائمة قيم مرنة: عرض + 🗑️ حذف + ➕ إضافة)
- 🧹 التنظيف (تعديل عدد رسائل التنظيف)

أنظمة أخرى مسجّلة في ملفات منفصلة (نفس router الرئيسي يُجمَّع في core/bot.py):
- members_panel.py -> 👥 الأعضاء
- moderators_panel.py -> 👮 الإداريين

كل نظام جديد يُبنى مستقبلاً يُضاف له:
1. زر في keyboards.py (main_menu_keyboard)
2. نص في notifications/messages.py
3. ملف/handler خاص به (أو هنا إن كان صغيراً)
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool, set_setting
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.states import OwnerStates
from systems.owner.notifications import messages
from systems.owner.utils import parse_number
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


@router.callback_query(F.data == "owner:noop")
async def noop(callback: CallbackQuery) -> None:
    """زر بدون أي إجراء (يُستخدم لعرض قيمة فقط بدون رد فعل)."""
    await callback.answer()


# ===== الرصيد =====

@router.callback_query(F.data == "owner:wallet")
async def show_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()

    total_balance = await wallet.get_total_balance(pool)
    top_members = await wallet.get_top_balances(pool, limit=10)

    text = messages.wallet_text(total_balance, len(top_members))

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


# ===== الخصم والمكافأة (قائمة قيم مرنة) =====

@router.callback_query(F.data == "owner:rewards")
async def show_rewards(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    amounts = await get_reward_amounts(pool)

    text = messages.rewards_text(amounts)

    await callback.message.edit_text(text, reply_markup=keyboards.rewards_keyboard(amounts))
    await callback.answer()


@router.callback_query(F.data.startswith("owner:rewards:remove:"))
async def remove_reward_amount(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    amount_to_remove = int(callback.data.split(":")[-1])

    pool = await get_pool()
    amounts = await get_reward_amounts(pool)

    if len(amounts) <= 1:
        await callback.answer(messages.REWARD_AMOUNT_MIN_REACHED, show_alert=True)
        return

    if amount_to_remove in amounts:
        amounts.remove(amount_to_remove)
        await set_setting(pool, REWARD_AMOUNTS_KEY, amounts)

    text = messages.rewards_text(amounts)
    await callback.message.edit_text(text, reply_markup=keyboards.rewards_keyboard(amounts))
    await callback.answer()


@router.callback_query(F.data == "owner:rewards:add")
async def add_reward_amount_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_new_reward_amount)

    await callback.message.edit_text(
        messages.REWARD_AMOUNT_ADD_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_new_reward_amount)
async def add_reward_amount_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    new_amount = parse_number(message.text) if message.text else None

    if new_amount is None or new_amount <= 0:
        await message.reply(
            messages.REWARD_AMOUNT_ADD_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    pool = await get_pool()
    amounts = await get_reward_amounts(pool)

    if new_amount in amounts:
        await message.reply(
            messages.REWARD_AMOUNT_ADD_DUPLICATE,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    amounts.append(new_amount)
    amounts.sort()

    await set_setting(pool, REWARD_AMOUNTS_KEY, amounts)
    await state.clear()

    await message.reply(
        messages.reward_amount_added_text(amounts),
        reply_markup=keyboards.rewards_keyboard(amounts),
    )


# ===== التنظيف =====

@router.callback_query(F.data == "owner:cleanup")
async def show_cleanup(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

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

    new_range = parse_number(message.text) if message.text else None

    if new_range is None or new_range <= 0:
        await message.reply(
            messages.CLEANUP_EDIT_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    pool = await get_pool()
    await set_setting(pool, CLEANUP_RANGE_KEY, new_range)

    await state.clear()

    await message.reply(
        messages.cleanup_updated_text(new_range),
        reply_markup=keyboards.back_keyboard(),
    )
