"""
لعبة الألغاز (riddles) - نفس آلية trivia تماماً لكن بمحتوى ألغاز مستقل.
"""

import asyncio
import random

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import CallbackQuery, Message

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.games import riddles_queries
from systems.games.notifications import riddles_messages as messages
from systems.protection.text_normalizer import normalize_text


router = Router(name="games_riddles")


_active_riddles: dict[int, dict] = {}


@router.callback_query(F.data.startswith("games:open:riddles:"))
async def start_riddle(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    pool = await get_pool()

    riddles = await riddles_queries.get_riddles(pool)

    if not riddles:
        await callback.answer()
        return

    chosen = random.choice(riddles)
    timeout = await riddles_queries.get_riddles_timeout(pool)

    chat_id = callback.message.chat.id

    sent = await callback.message.edit_text(messages.riddle_text(chosen["question"], timeout))

    _active_riddles[chat_id] = {
        "owner_id": owner_id,
        "answers": chosen["answers"],
        "reward": chosen.get("reward", 1500),
        "answered": False,
    }

    await callback.answer()

    asyncio.create_task(_end_after_timeout(chat_id, timeout, sent))


async def _end_after_timeout(chat_id: int, timeout: int, sent_message: Message) -> None:
    await asyncio.sleep(timeout)

    state = _active_riddles.get(chat_id)

    if state is None or state["answered"]:
        return

    _active_riddles.pop(chat_id, None)

    try:
        await sent_message.edit_text(messages.TIME_UP_TEXT)
    except Exception:
        pass


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def receive_riddle_answer(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise SkipHandler

    chat_id = message.chat.id
    state = _active_riddles.get(chat_id)

    if state is None or state["answered"]:
        raise SkipHandler

    if message.from_user.id != state["owner_id"]:
        raise SkipHandler

    normalized_answer = normalize_text(message.text)

    is_correct = any(
        normalized_answer == normalize_text(correct) or normalize_text(correct) in normalized_answer
        for correct in state["answers"]
    )

    if not is_correct:
        raise SkipHandler

    state["answered"] = True
    _active_riddles.pop(chat_id, None)

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    await wallet.add_balance(pool, message.from_user.id, state["reward"])
    await members_queries.increment_games_played(pool, message.from_user.id)
    await members_queries.increment_games_won(pool, message.from_user.id)
    await members_queries.update_last_game_at(pool, message.from_user.id)

    await message.reply(
        messages.correct_answer_text(message.from_user.full_name, state["reward"])
    )
