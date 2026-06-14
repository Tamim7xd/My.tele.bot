"""
لوحة التحكم - نظام المستويات (levels).

يحتوي على:
- 📊 المستويات: عرض الإعدادات الحالية + تعديل كل قيمة

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
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
from systems.levels import levels


router = Router(name="owner_levels")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


async def _show_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()

    tier_1_5 = await levels.get_messages_tier_1_5(pool)
    tier_6_plus = await levels.get_messages_tier_6_plus(pool)
    reward = await levels.get_level_up_reward(pool)

    text = messages.levels_settings_text(tier_1_5, tier_6_plus, reward)
    keyboard = keyboards.levels_settings_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "owner:levels")
async def show_levels(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await _show_settings(callback)
    await callback.answer()


@router.callback_query(F.data == "owner:levels:edit_tier1")
async def edit_tier1_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_levels_tier1)

    await callback.message.edit_text(
        messages.LEVELS_EDIT_TIER_1_5_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_levels_tier1)
async def receive_tier1(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(messages.LEVELS_EDIT_INVALID, reply_markup=keyboards.cancel_edit_keyboard())
        return

    pool = await get_pool()
    await set_setting(pool, levels.MESSAGES_TIER_1_5_KEY, value)
    await state.clear()

    tier_1_5 = await levels.get_messages_tier_1_5(pool)
    tier_6_plus = await levels.get_messages_tier_6_plus(pool)
    reward = await levels.get_level_up_reward(pool)

    await message.reply(
        messages.levels_updated_text(tier_1_5, tier_6_plus, reward),
        reply_markup=keyboards.levels_settings_keyboard(),
    )


@router.callback_query(F.data == "owner:levels:edit_tier2")
async def edit_tier2_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_levels_tier2)

    await callback.message.edit_text(
        messages.LEVELS_EDIT_TIER_6_PLUS_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_levels_tier2)
async def receive_tier2(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(messages.LEVELS_EDIT_INVALID, reply_markup=keyboards.cancel_edit_keyboard())
        return

    pool = await get_pool()
    await set_setting(pool, levels.MESSAGES_TIER_6_PLUS_KEY, value)
    await state.clear()

    tier_1_5 = await levels.get_messages_tier_1_5(pool)
    tier_6_plus = await levels.get_messages_tier_6_plus(pool)
    reward = await levels.get_level_up_reward(pool)

    await message.reply(
        messages.levels_updated_text(tier_1_5, tier_6_plus, reward),
        reply_markup=keyboards.levels_settings_keyboard(),
    )


@router.callback_query(F.data == "owner:levels:edit_reward")
async def edit_reward_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_levels_reward)

    await callback.message.edit_text(
        messages.LEVELS_EDIT_REWARD_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_levels_reward)
async def receive_reward(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(messages.LEVELS_EDIT_INVALID, reply_markup=keyboards.cancel_edit_keyboard())
        return

    pool = await get_pool()
    await set_setting(pool, levels.LEVEL_UP_REWARD_KEY, value)
    await state.clear()

    tier_1_5 = await levels.get_messages_tier_1_5(pool)
    tier_6_plus = await levels.get_messages_tier_6_plus(pool)
    reward = await levels.get_level_up_reward(pool)

    await message.reply(
        messages.levels_updated_text(tier_1_5, tier_6_plus, reward),
        reply_markup=keyboards.levels_settings_keyboard(),
    )
