"""
لعبة حجر ورقة مقص (rps) - اللعبة المشتركة الوحيدة (تتيح لعضو آخر المشاركة).

التدفق:
1. عضو يفتح "لعبة" -> يضغط "🪨📄✂️ حجر ورقة مقص"
2. تظهر أزرار 🪨 حجر / 📄 ورقة / ✂️ مقص لصاحب اللعبة
3. بعد اختياره، تتحول الرسالة لدعوة عامة بنفس الأزرار مفتوحة لأي عضو آخر
4. أول عضو آخر يضغط زراً يُحسب كالخصم تلقائياً
5. تُحسب النتيجة وتُعرض بشكل مرتب (الفائز + المكافأة)، تعادل = لا مكافأة
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.games import rps_queries
from systems.games.notifications import rps_messages as messages


router = Router(name="games_rps")


CHOICES = {"rock": "🪨 حجر", "paper": "📄 ورقة", "scissors": "✂️ مقص"}

_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


# {chat_id: {"owner_id": int, "owner_choice": str, "owner_name": str}}
_pending_challenges: dict[int, dict] = {}


def _choice_keyboard(stage: str, owner_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"games:rps:{stage}:{key}:{owner_id}")]
        for key, label in CHOICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("games:open:rps:"))
async def start_rps(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    keyboard = _choice_keyboard("pick1", owner_id)
    await callback.message.edit_text(messages.PICK_CHOICE_TEXT, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("games:rps:pick1:"))
async def owner_picks(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    _, _, _, choice_key, owner_id_str = callback.data.split(":")
    owner_id = int(owner_id_str)

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    chat_id = callback.message.chat.id

    _pending_challenges[chat_id] = {
        "owner_id": owner_id,
        "owner_choice": choice_key,
        "owner_name": callback.from_user.full_name,
    }

    keyboard = _choice_keyboard("challenge", owner_id)
    await callback.message.edit_text(
        messages.waiting_challenger_text(callback.from_user.full_name),
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("games:rps:challenge:"))
async def challenger_picks(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    _, _, _, choice_key, owner_id_str = callback.data.split(":")
    owner_id = int(owner_id_str)

    chat_id = callback.message.chat.id
    pending = _pending_challenges.get(chat_id)

    if pending is None or pending["owner_id"] != owner_id:
        await callback.answer()
        return

    if callback.from_user.id == owner_id:
        await callback.answer()
        return

    _pending_challenges.pop(chat_id, None)

    owner_choice = pending["owner_choice"]
    owner_name = pending["owner_name"]
    challenger_choice = choice_key
    challenger_name = callback.from_user.full_name

    pool = await get_pool()

    await members_queries.ensure_member_exists(
        pool, user_id=owner_id, username=None, full_name=owner_name,
    )
    await members_queries.ensure_member_exists(
        pool, user_id=callback.from_user.id, username=callback.from_user.username, full_name=challenger_name,
    )

    reward = await rps_queries.get_rps_reward(pool)

    if owner_choice == challenger_choice:
        result_text = messages.draw_text(owner_name, challenger_name, CHOICES[owner_choice])
        await members_queries.increment_games_played(pool, owner_id)
        await members_queries.increment_games_played(pool, callback.from_user.id)

    elif _BEATS[owner_choice] == challenger_choice:
        await wallet.add_balance(pool, owner_id, reward)
        await members_queries.increment_games_played(pool, owner_id)
        await members_queries.increment_games_won(pool, owner_id)
        await members_queries.increment_games_played(pool, callback.from_user.id)

        result_text = messages.winner_text(
            winner_name=owner_name, loser_name=challenger_name,
            winner_choice=CHOICES[owner_choice], loser_choice=CHOICES[challenger_choice],
            reward=reward,
        )

    else:
        await wallet.add_balance(pool, callback.from_user.id, reward)
        await members_queries.increment_games_played(pool, callback.from_user.id)
        await members_queries.increment_games_won(pool, callback.from_user.id)
        await members_queries.increment_games_played(pool, owner_id)

        result_text = messages.winner_text(
            winner_name=challenger_name, loser_name=owner_name,
            winner_choice=CHOICES[challenger_choice], loser_choice=CHOICES[owner_choice],
            reward=reward,
        )

    await members_queries.update_last_game_at(pool, owner_id)

    await callback.message.edit_text(result_text)
    await callback.answer()
