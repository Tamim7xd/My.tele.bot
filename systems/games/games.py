"""
نظام الألعاب (games) - الملف الرئيسي.

كلمات التشغيل: "لعبة"، "العاب"، "العب"، "لعبه"
تفتح قائمة اختيار اللعبة - حصرية لمن كتب الأمر فقط (owner_id محفوظ
في كل callback_data، وأي عضو آخر يضغط يُتجاهل بصمت تام).

القائمة تُغلق تلقائياً (تعديل لرسالة "انتهى الوقت") إن لم يُختار
شيء خلال GAME_SELECTION_TIMEOUT ثوانٍ (3 ثوانٍ افتراضياً).

فترة الانتظار العامة (cooldown، 10 ثوانٍ افتراضياً) تُطبَّق على فتح
أي لعبة جديدة (من القائمة)، ليس بين الجولات داخل اللعبة نفسها.

كل لعبة لها ملفها المستقل (trivia.py, rps.py, lucky_box.py,
riddles.py, last_survivor.py) ويُسجَّل كـ router مستقل في core/bot.py.
هذا الملف فقط يعرض القائمة، وكل ملف لعبة يستقبل بنفسه
callback "games:open:{game_key}:{owner_id}" الخاص به.
"""

import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from systems.games import queries as games_queries
from systems.games import keyboards as games_keyboards
from systems.games.notifications import messages


router = Router(name="games")


TRIGGER_WORDS = {"لعبة", "العاب", "العب", "لعبه"}


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.in_(TRIGGER_WORDS))
async def open_games_menu(message: Message) -> None:
    if message.from_user is None:
        return

    pool = await get_pool()
    user_id = message.from_user.id

    cooldown = await games_queries.get_games_cooldown(pool)

    if not await _can_open(pool, user_id, cooldown):
        await message.reply(messages.COOLDOWN_MESSAGE)
        return

    enabled_games = await games_queries.get_enabled_games(pool)

    if not any(enabled_games.values()):
        return

    keyboard = games_keyboards.games_menu_keyboard(user_id, enabled_games)
    sent = await message.reply(messages.GAMES_MENU_TEXT, reply_markup=keyboard)

    asyncio.create_task(_expire_menu(sent, user_id))


async def _can_open(pool, user_id: int, cooldown: int) -> bool:
    from systems.members.queries import can_play_game
    return await can_play_game(pool, user_id, cooldown)


async def _expire_menu(message: Message, owner_id: int) -> None:
    """
    يغلق قائمة اختيار اللعبة تلقائياً بعد GAME_SELECTION_TIMEOUT ثوانٍ،
    فقط إذا لم يتم اختيار أي لعبة بعد (نتحقق أن نص الرسالة لم يتغيّر).
    """
    await asyncio.sleep(games_queries.GAME_SELECTION_TIMEOUT)

    try:
        current_text = message.text or message.html_text

        if current_text and messages.GAMES_MENU_TEXT.split("\n")[0] in current_text:
            await message.edit_text(messages.MENU_EXPIRED)
    except Exception:
        pass


@router.callback_query(F.data == "games:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
