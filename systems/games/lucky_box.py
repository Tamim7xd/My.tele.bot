"""
صندوق الحظ (lucky_box).

التدفق:
1. عضو يفتح "لعبة" -> يضغط "📦 صندوق الحظ"
2. تظهر رسوم الدخول + زر "ابدأ اللعبة" - حصرية لصاحب اللعبة
3. عند الضغط: يتحقق من كفاية الرصيد، يخصم الرسوم
4. يختار نتيجة عشوائية موزونة (نسب من اللوحة) ويعرضها
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.games import lucky_box_queries
from systems.games.notifications import lucky_box_messages as messages


router = Router(name="games_lucky_box")


def _start_keyboard(owner_id: int, fee: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💰 رسوم الدخول: {fee:,}", callback_data="games:noop")],
            [InlineKeyboardButton(text="🎁 ابدأ اللعبة", callback_data=f"games:lucky_box:play:{owner_id}")],
        ]
    )


@router.callback_query(F.data.startswith("games:open:lucky_box:"))
async def start_lucky_box(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    pool = await get_pool()
    fee = await lucky_box_queries.get_entry_fee(pool)

    keyboard = _start_keyboard(owner_id, fee)
    await callback.message.edit_text(messages.INTRO_TEXT, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("games:lucky_box:play:"))
async def play_lucky_box(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=owner_id, username=callback.from_user.username, full_name=callback.from_user.full_name,
    )

    fee = await lucky_box_queries.get_entry_fee(pool)
    current_balance = await wallet.get_balance(pool, owner_id)

    if current_balance < fee:
        await callback.answer(messages.INSUFFICIENT_BALANCE, show_alert=True)
        return

    await wallet.deduct_balance(pool, owner_id, fee)

    outcomes = await lucky_box_queries.get_outcomes(pool)
    outcome = lucky_box_queries.pick_outcome(outcomes)

    won_amount = outcome["amount"]

    if won_amount > 0:
        await wallet.add_balance(pool, owner_id, won_amount)

    await members_queries.increment_games_played(pool, owner_id)

    if won_amount > fee:
        await members_queries.increment_games_won(pool, owner_id)

    await members_queries.update_last_game_at(pool, owner_id)

    net = won_amount - fee

    await callback.message.edit_text(messages.result_text(won_amount, net))
    await callback.answer()
