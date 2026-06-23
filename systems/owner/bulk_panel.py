"""
لوحة التحكم - المكافأة/الخصم الجماعي.

يرسل مكافأة أو يخصم مبلغاً من رصيد كل الأعضاء المسجلين دفعة واحدة.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.owner.utils import parse_number
from systems.members import queries as members_queries
from systems.wallet import wallet


router = Router(name="owner_bulk")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


def _bulk_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 مكافأة جماعية", callback_data="owner:bulk_reward")],
            [InlineKeyboardButton(text="💸 خصم جماعي", callback_data="owner:bulk_deduct")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def _cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:bulk_action")],
        ]
    )


@router.callback_query(F.data == "owner:bulk_action")
async def show_bulk_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    count = await members_queries.get_members_count(pool)

    text = (
        f"🎁 <b>المكافأة/الخصم الجماعي</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 عدد الأعضاء: {count:,}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر العملية:"
    )

    await callback.message.edit_text(text, reply_markup=_bulk_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:bulk_reward")
async def bulk_reward_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_bulk_reward_amount)
    await callback.message.edit_text(
        "🎁 أرسل المبلغ للمكافأة الجماعية (يدعم 1.000):",
        reply_markup=_cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_bulk_reward_amount)
async def bulk_reward_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    amount = parse_number(message.text) if message.text else None

    if amount is None or amount <= 0:
        await message.reply("❌ مبلغ غير صحيح.", reply_markup=_cancel_keyboard())
        return

    await state.clear()

    pool = await get_pool()
    members = await _get_all_members(pool)

    success = 0
    for member in members:
        try:
            await wallet.add_balance(pool, member["user_id"], amount)
            success += 1
        except Exception:
            pass

    await message.reply(
        f"✅ تم إرسال مكافأة {amount:,} د.ع لـ {success:,} عضو.",
        reply_markup=_bulk_main_keyboard(),
    )


@router.callback_query(F.data == "owner:bulk_deduct")
async def bulk_deduct_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_bulk_deduct_amount)
    await callback.message.edit_text(
        "💸 أرسل المبلغ للخصم الجماعي (يدعم 1.000):",
        reply_markup=_cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_bulk_deduct_amount)
async def bulk_deduct_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    amount = parse_number(message.text) if message.text else None

    if amount is None or amount <= 0:
        await message.reply("❌ مبلغ غير صحيح.", reply_markup=_cancel_keyboard())
        return

    await state.clear()

    pool = await get_pool()
    members = await _get_all_members(pool)

    success = 0
    for member in members:
        try:
            current = await wallet.get_balance(pool, member["user_id"])
            deduct = min(amount, current)
            if deduct > 0:
                await wallet.deduct_balance(pool, member["user_id"], deduct)
            success += 1
        except Exception:
            pass

    await message.reply(
        f"✅ تم خصم {amount:,} د.ع من {success:,} عضو.",
        reply_markup=_bulk_main_keyboard(),
    )


async def _get_all_members(pool) -> list:
    """يرجع كل الأعضاء المسجلين (بدون حد أقصى)."""
    import asyncpg

    async with pool.acquire() as conn:
        return await conn.fetch("SELECT user_id FROM members")
