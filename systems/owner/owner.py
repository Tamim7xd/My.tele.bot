"""
لوحة التحكم - الملف الرئيسي.

كلمة التشغيل: "admin" (إنجليزي فقط، بدون "/")
- في الخاص: المالك يكتب "admin" -> تفتح لوحة التحكم في الخاص
- في المجموعة: المالك يكتب "admin" -> تفتح لوحة التحكم داخل المجموعة

كل نظام جديد يُبنى مستقبلاً يُضاف له:
1. زر في keyboards.py (main_menu_keyboard)
2. نص في notifications/messages.py
3. handler هنا لعرض تفاصيله عند الضغط على الزر

بدون التأثير على الأنظمة الأخرى الموجودة في اللوحة.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.notifications import messages
from systems.moderators import queries as moderators_queries
from systems.wallet import wallet
from systems.rewards.keyboards import REWARD_AMOUNTS
from systems.cleanup.cleanup import CLEANUP_RANGE


router = Router(name="owner")


TRIGGER_WORD = "admin"


@router.message(F.text == TRIGGER_WORD)
async def open_panel(message: Message) -> None:
    """يفتح لوحة التحكم الرئيسية - المالك فقط، في الخاص أو المجموعة."""
    if message.from_user is None:
        return

    if message.from_user.id != OWNER_ID:
        return

    await message.answer(messages.MAIN_MENU_TEXT, reply_markup=keyboards.main_menu_keyboard())


@router.callback_query(F.data == "owner:main")
async def back_to_main(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    if callback.from_user.id != OWNER_ID:
        await callback.answer()
        return

    await callback.message.edit_text(messages.MAIN_MENU_TEXT, reply_markup=keyboards.main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:moderators")
async def show_moderators(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    if callback.from_user.id != OWNER_ID:
        await callback.answer()
        return

    pool = await get_pool()

    admin_count = await moderators_queries.get_staff_count(pool, "admin")
    moderator_count = await moderators_queries.get_staff_count(pool, "moderator")

    text = messages.moderators_text(admin_count, moderator_count)

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:wallet")
async def show_wallet(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    if callback.from_user.id != OWNER_ID:
        await callback.answer()
        return

    pool = await get_pool()

    total_balance = await wallet.get_total_balance(pool)
    top_members = await wallet.get_top_balances(pool, limit=10)

    text = messages.wallet_text(total_balance, len(top_members))

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:rewards")
async def show_rewards(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    if callback.from_user.id != OWNER_ID:
        await callback.answer()
        return

    text = messages.rewards_text(REWARD_AMOUNTS)

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "owner:cleanup")
async def show_cleanup(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    if callback.from_user.id != OWNER_ID:
        await callback.answer()
        return

    text = messages.cleanup_text(CLEANUP_RANGE)

    await callback.message.edit_text(text, reply_markup=keyboards.back_keyboard())
    await callback.answer()
