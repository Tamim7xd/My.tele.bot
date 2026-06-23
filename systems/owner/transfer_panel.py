"""
لوحة التحكم - نظام التحويل (transfer).
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.owner.utils import parse_number
from systems.transfer import queries as transfer_queries


router = Router(name="owner_transfer")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


def _transfer_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📉 الحد الأدنى", callback_data="owner:transfer_min")],
            [InlineKeyboardButton(text="📈 الحد الأقصى", callback_data="owner:transfer_max")],
            [InlineKeyboardButton(text="💸 نسبة الرسوم", callback_data="owner:transfer_fee")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def _cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:transfer")],
        ]
    )


@router.callback_query(F.data == "owner:transfer")
async def show_transfer_settings(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    min_amount = await transfer_queries.get_min_transfer(pool)
    max_amount = await transfer_queries.get_max_transfer(pool)
    fee_percent = await transfer_queries.get_fee_percent(pool)

    max_text = f"{max_amount:,} د.ع" if max_amount > 0 else "بلا حد"

    text = (
        f"💸 <b>إعدادات التحويل</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📉 الحد الأدنى: {min_amount:,} د.ع\n"
        f"📈 الحد الأقصى: {max_text}\n"
        f"💸 الرسوم: {fee_percent}%\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )

    await callback.message.edit_text(text, reply_markup=_transfer_settings_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:transfer_min")
async def transfer_min_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_transfer_min)
    await callback.message.edit_text("✏️ أرسل الحد الأدنى للتحويل (يدعم 1.000):", reply_markup=_cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_transfer_min)
async def transfer_min_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value < 0:
        await message.reply("❌ رقم غير صحيح.", reply_markup=_cancel_keyboard())
        return

    pool = await get_pool()
    await transfer_queries.set_min_transfer(pool, value)
    await state.clear()

    await message.reply(f"✅ تم تحديث الحد الأدنى إلى: {value:,} د.ع", reply_markup=_transfer_settings_keyboard())


@router.callback_query(F.data == "owner:transfer_max")
async def transfer_max_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_transfer_max)
    await callback.message.edit_text("✏️ أرسل الحد الأقصى للتحويل (0 = بلا حد):", reply_markup=_cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_transfer_max)
async def transfer_max_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None:
        await message.reply("❌ رقم غير صحيح.", reply_markup=_cancel_keyboard())
        return

    pool = await get_pool()
    await transfer_queries.set_max_transfer(pool, value)
    await state.clear()

    max_text = f"{value:,} د.ع" if value > 0 else "بلا حد"
    await message.reply(f"✅ تم تحديث الحد الأقصى إلى: {max_text}", reply_markup=_transfer_settings_keyboard())


@router.callback_query(F.data == "owner:transfer_fee")
async def transfer_fee_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_transfer_fee)
    await callback.message.edit_text("✏️ أرسل نسبة الرسوم % (0 = بدون رسوم):", reply_markup=_cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_transfer_fee)
async def transfer_fee_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value > 100:
        await message.reply("❌ نسبة غير صحيحة (0-100).", reply_markup=_cancel_keyboard())
        return

    pool = await get_pool()
    await transfer_queries.set_fee_percent(pool, value)
    await state.clear()

    await message.reply(f"✅ تم تحديث الرسوم إلى: {value}%", reply_markup=_transfer_settings_keyboard())
