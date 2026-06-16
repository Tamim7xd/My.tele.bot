"""
الناجي الأخير (last_survivor) - لعبة جماعية.

التدفق:
1. عضو يفتح "لعبة" -> يضغط "🧟 الناجي الأخير"
2. إعلان جماعي: "بدأت اللعبة! ادفع [رسوم] للانضمام" + زر "🙋 انضم" مفتوح للجميع
3. نافذة انضمام (30 ثانية افتراضياً)، العداد يتحدث: "👥 المنضمون: N"
4. عند انتهاء النافذة:
   - أقل من الحد الأدنى -> تُلغى اللعبة وتُرجَع الرسوم لكل من دفع
   - كافٍ -> جولات حذف تدريجي (دراما) حتى يتبقى ناجٍ واحد يربح كل الوعاء
"""

import asyncio
import random

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.games import last_survivor_queries as ls_queries
from systems.games.notifications import last_survivor_messages as messages


router = Router(name="games_last_survivor")


_active_games: dict[int, dict] = {}


def _join_keyboard(player_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🙋 انضم ({player_count})", callback_data="games:ls:join")],
        ]
    )


@router.callback_query(F.data.startswith("games:open:last_survivor:"))
async def start_last_survivor(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    chat_id = callback.message.chat.id

    if chat_id in _active_games and not _active_games[chat_id].get("closed", True):
        await callback.answer()
        return

    pool = await get_pool()
    fee = await ls_queries.get_entry_fee(pool)
    join_window = await ls_queries.get_join_window(pool)

    sent = await callback.message.edit_text(
        messages.announcement_text(fee, join_window),
        reply_markup=_join_keyboard(0),
    )

    _active_games[chat_id] = {
        "players": {},
        "fee": fee,
        "closed": False,
        "message_id": sent.message_id,
    }

    await callback.answer()

    asyncio.create_task(_close_join_window(chat_id, join_window, sent))


@router.callback_query(F.data == "games:ls:join")
async def join_game(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    state = _active_games.get(chat_id)

    if state is None or state["closed"]:
        await callback.answer()
        return

    user_id = callback.from_user.id

    if user_id in state["players"]:
        await callback.answer(messages.ALREADY_JOINED)
        return

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=user_id, username=callback.from_user.username, full_name=callback.from_user.full_name,
    )

    balance = await wallet.get_balance(pool, user_id)
    fee = state["fee"]

    if balance < fee:
        await callback.answer(messages.INSUFFICIENT_BALANCE, show_alert=True)
        return

    await wallet.deduct_balance(pool, user_id, fee)

    state["players"][user_id] = callback.from_user.full_name

    try:
        await callback.message.edit_reply_markup(reply_markup=_join_keyboard(len(state["players"])))
    except Exception:
        pass

    await callback.answer(messages.JOINED_SUCCESS)


async def _close_join_window(chat_id: int, join_window: int, sent_message: Message) -> None:
    await asyncio.sleep(join_window)

    state = _active_games.get(chat_id)

    if state is None:
        return

    state["closed"] = True

    pool = await get_pool()
    min_players = await ls_queries.get_min_players(pool)

    players = state["players"]

    if len(players) < min_players:
        for user_id in players:
            await wallet.add_balance(pool, user_id, state["fee"])

        try:
            await sent_message.edit_text(messages.cancelled_text(len(players), min_players))
        except Exception:
            pass

        _active_games.pop(chat_id, None)
        return

    try:
        await sent_message.edit_text(messages.starting_text(len(players)))
    except Exception:
        pass

    await asyncio.sleep(1)

    await _run_elimination(chat_id, sent_message)


async def _run_elimination(chat_id: int, sent_message: Message) -> None:
    state = _active_games.get(chat_id)

    if state is None:
        return

    pool = await get_pool()
    delay = await ls_queries.get_elimination_delay(pool)

    players = dict(state["players"])
    pot = state["fee"] * len(players)

    remaining = list(players.items())
    random.shuffle(remaining)

    for user_id in players:
        await members_queries.increment_games_played(pool, user_id)

    eliminated_log = []

    while len(remaining) > 1:
        await asyncio.sleep(delay)

        eliminated_user_id, eliminated_name = remaining.pop(0)
        eliminated_log.append(eliminated_name)

        try:
            await sent_message.edit_text(
                messages.elimination_progress_text(eliminated_name, len(remaining), eliminated_log)
            )
        except Exception:
            pass

    await asyncio.sleep(delay)

    winner_id, winner_name = remaining[0]

    await wallet.add_balance(pool, winner_id, pot)
    await members_queries.increment_games_won(pool, winner_id)
    await members_queries.update_last_game_at(pool, winner_id)

    try:
        await sent_message.edit_text(messages.winner_text(winner_name, pot))
    except Exception:
        pass

    _active_games.pop(chat_id, None)
