"""
لعبة الأسئلة المرحة (trivia).

التدفق:
1. عضو يفتح "لعبة" -> يضغط "🧠 أسئلة مرحة"
2. يظهر سؤال عشوائي + مهلة (5 ثوانٍ افتراضياً)
3. فقط صاحب اللعبة (owner_id) يمكنه الإجابة - بالرد على رسالة السؤال
   أو بدون رد (أي رسالة عادية منه خلال المهلة) - أي عضو آخر يُتجاهل تماماً
4. الجواب يُطبَّع (نفس محرك التطبيع في الحماية) للتعرف على صيغ مختلفة
5. إجابة صحيحة -> مكافأة + إعلان الفوز
   إجابة خاطئة أو انتهاء الوقت -> إعلان فشل/انتهاء بدون مكافأة

state بسيط: نخزن في الذاكرة (dict) السؤال الجاري لكل محادثة + صاحبه،
لأن اللعبة قصيرة العمر (ثوانٍ معدودة) ولا تحتاج تخزين دائم في قاعدة البيانات.
"""

import asyncio
import random

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import CallbackQuery, Message

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.games import trivia_queries
from systems.games.notifications import trivia_messages as messages
from systems.protection.text_normalizer import normalize_text


router = Router(name="games_trivia")


# {chat_id: {"owner_id": int, "answers": [...], "reward": int, "answered": bool, "message_id": int}}
_active_questions: dict[int, dict] = {}


@router.callback_query(F.data.startswith("games:open:trivia:"))
async def start_trivia(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    owner_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    pool = await get_pool()

    questions = await trivia_queries.get_questions(pool)

    if not questions:
        await callback.answer()
        return

    chosen = random.choice(questions)
    timeout = await trivia_queries.get_trivia_timeout(pool)

    chat_id = callback.message.chat.id

    sent = await callback.message.edit_text(messages.question_text(chosen["question"], timeout))

    _active_questions[chat_id] = {
        "owner_id": owner_id,
        "answers": chosen["answers"],
        "reward": chosen.get("reward", 1000),
        "answered": False,
        "message_id": sent.message_id,
    }

    await callback.answer()

    asyncio.create_task(_end_after_timeout(chat_id, timeout, sent))


async def _end_after_timeout(chat_id: int, timeout: int, sent_message: Message) -> None:
    await asyncio.sleep(timeout)

    state = _active_questions.get(chat_id)

    if state is None or state["answered"]:
        return

    _active_questions.pop(chat_id, None)

    try:
        await sent_message.edit_text(messages.TIME_UP_TEXT)
    except Exception:
        pass


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def receive_answer(message: Message) -> None:
    if message.from_user is None or message.text is None:
        raise SkipHandler

    chat_id = message.chat.id
    state = _active_questions.get(chat_id)

    if state is None or state["answered"]:
        raise SkipHandler

    # فقط صاحب اللعبة يمكنه الإجابة - أي عضو آخر يُتجاهل تماماً (لكن نمرر الرسالة)
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
    _active_questions.pop(chat_id, None)

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
