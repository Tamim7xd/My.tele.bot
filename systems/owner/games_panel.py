"""
لوحة التحكم - نظام الألعاب (games).

يحتوي على:
- 🎮 الألعاب: تفعيل/تعطيل كل لعبة + ⏱️ فترة الانتظار العامة
- ⚙️ إعدادات كل لعبة (مكافآت، رسوم، أسئلة، مهلات...)

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.owner.utils import parse_number
from systems.owner import games_panel_keyboards as gkeyboards
from systems.owner import games_panel_messages as gmessages
from systems.games import queries as games_queries
from systems.games import trivia_queries
from systems.games import riddles_queries
from systems.games import rps_queries
from systems.games import lucky_box_queries
from systems.games import last_survivor_queries as ls_queries


router = Router(name="owner_games")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== القائمة الرئيسية =====

@router.callback_query(F.data == "owner:games")
async def show_games_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    cooldown = await games_queries.get_games_cooldown(pool)
    enabled_games = await games_queries.get_enabled_games(pool)

    text = gmessages.games_main_text(cooldown)
    keyboard = gkeyboards.games_main_keyboard(enabled_games)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:game_toggle:"))
async def toggle_game(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    game_key = callback.data.split(":")[-1]

    pool = await get_pool()
    await games_queries.toggle_game_enabled(pool, game_key)

    cooldown = await games_queries.get_games_cooldown(pool)
    enabled_games = await games_queries.get_enabled_games(pool)

    text = gmessages.games_main_text(cooldown)
    keyboard = gkeyboards.games_main_keyboard(enabled_games)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "owner:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ===== فترة الانتظار العامة =====

@router.callback_query(F.data == "owner:games_cooldown")
async def cooldown_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_games_cooldown)

    await callback.message.edit_text(gmessages.COOLDOWN_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_games_cooldown)
async def cooldown_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value < 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await games_queries.set_games_cooldown(pool, value)
    await state.clear()

    await message.reply(gmessages.cooldown_updated_text(value), reply_markup=gkeyboards.back_to_games_keyboard())


# ===== توجيه لإعدادات كل لعبة =====

@router.callback_query(F.data.startswith("owner:game_settings:"))
async def open_game_settings(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    game_key = callback.data.split(":")[-1]

    if game_key == "trivia":
        await _show_trivia_settings(callback)
    elif game_key == "riddles":
        await _show_riddles_settings(callback)
    elif game_key == "rps":
        await _show_rps_settings(callback)
    elif game_key == "lucky_box":
        await _show_lucky_box_settings(callback)
    elif game_key == "last_survivor":
        await _show_ls_settings(callback)

    await callback.answer()


# ===== أسئلة مرحة (trivia) =====

async def _show_trivia_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()
    questions = await trivia_queries.get_questions(pool)
    timeout = await trivia_queries.get_trivia_timeout(pool)

    text = gmessages.questions_settings_text("🧠 <b>أسئلة مرحة</b>", questions, timeout)
    keyboard = gkeyboards.questions_list_keyboard(questions, "trivia", "owner:games")

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:trivia_remove:"))
async def trivia_remove(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    pool = await get_pool()
    await trivia_queries.delete_question(pool, index)

    await _show_trivia_settings(callback)
    await callback.answer(gmessages.question_removed_text())


@router.callback_query(F.data == "owner:trivia_add")
async def trivia_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_trivia_question)
    await callback.message.edit_text(gmessages.QUESTION_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_trivia_question)
async def trivia_question_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    await state.update_data(new_question=message.text)
    await state.set_state(OwnerStates.waiting_trivia_answers)

    await message.reply(gmessages.ANSWERS_PROMPT, reply_markup=gkeyboards.cancel_keyboard())


@router.message(OwnerStates.waiting_trivia_answers)
async def trivia_answers_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    answers = [a.strip() for a in message.text.split(",") if a.strip()]

    if not answers:
        await message.reply(gmessages.ANSWERS_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
        return

    await state.update_data(new_answers=answers)
    await state.set_state(OwnerStates.waiting_trivia_reward)

    await message.reply(gmessages.REWARD_PROMPT, reply_markup=gkeyboards.cancel_keyboard())


@router.message(OwnerStates.waiting_trivia_reward)
async def trivia_reward_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    reward = parse_number(message.text) if message.text else None

    if reward is None or reward <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    question = data.get("new_question")
    answers = data.get("new_answers")

    pool = await get_pool()
    await trivia_queries.add_question(pool, question, answers, reward)
    await state.clear()

    questions = await trivia_queries.get_questions(pool)

    await message.reply(
        gmessages.question_added_text(question),
        reply_markup=gkeyboards.questions_list_keyboard(questions, "trivia", "owner:games"),
    )


@router.callback_query(F.data == "owner:trivia_timeout")
async def trivia_timeout_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_trivia_timeout)
    await callback.message.edit_text(gmessages.TIMEOUT_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_trivia_timeout)
async def trivia_timeout_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    seconds = parse_number(message.text) if message.text else None

    if seconds is None or seconds <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await trivia_queries.set_trivia_timeout(pool, seconds)
    await state.clear()

    await message.reply(gmessages.timeout_updated_text(seconds), reply_markup=gkeyboards.back_to_games_keyboard())


# ===== الألغاز (riddles) =====

async def _show_riddles_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()
    riddles = await riddles_queries.get_riddles(pool)
    timeout = await riddles_queries.get_riddles_timeout(pool)

    text = gmessages.questions_settings_text("🧩 <b>الألغاز</b>", riddles, timeout)
    keyboard = gkeyboards.questions_list_keyboard(riddles, "riddles", "owner:games")

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:riddles_remove:"))
async def riddles_remove(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    pool = await get_pool()
    await riddles_queries.delete_riddle(pool, index)

    await _show_riddles_settings(callback)
    await callback.answer(gmessages.question_removed_text())


@router.callback_query(F.data == "owner:riddles_add")
async def riddles_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_riddle_question)
    await callback.message.edit_text(gmessages.QUESTION_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_riddle_question)
async def riddle_question_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    await state.update_data(new_riddle=message.text)
    await state.set_state(OwnerStates.waiting_riddle_answers)

    await message.reply(gmessages.ANSWERS_PROMPT, reply_markup=gkeyboards.cancel_keyboard())


@router.message(OwnerStates.waiting_riddle_answers)
async def riddle_answers_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    answers = [a.strip() for a in message.text.split(",") if a.strip()]

    if not answers:
        await message.reply(gmessages.ANSWERS_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
        return

    await state.update_data(new_riddle_answers=answers)
    await state.set_state(OwnerStates.waiting_riddle_reward)

    await message.reply(gmessages.REWARD_PROMPT, reply_markup=gkeyboards.cancel_keyboard())


@router.message(OwnerStates.waiting_riddle_reward)
async def riddle_reward_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    reward = parse_number(message.text) if message.text else None

    if reward is None or reward <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    riddle = data.get("new_riddle")
    answers = data.get("new_riddle_answers")

    pool = await get_pool()
    await riddles_queries.add_riddle(pool, riddle, answers, reward)
    await state.clear()

    riddles = await riddles_queries.get_riddles(pool)

    await message.reply(
        gmessages.question_added_text(riddle),
        reply_markup=gkeyboards.questions_list_keyboard(riddles, "riddles", "owner:games"),
    )


@router.callback_query(F.data == "owner:riddles_timeout")
async def riddles_timeout_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_riddles_timeout)
    await callback.message.edit_text(gmessages.TIMEOUT_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_riddles_timeout)
async def riddles_timeout_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    seconds = parse_number(message.text) if message.text else None

    if seconds is None or seconds <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await riddles_queries.set_riddles_timeout(pool, seconds)
    await state.clear()

    await message.reply(gmessages.timeout_updated_text(seconds), reply_markup=gkeyboards.back_to_games_keyboard())


# ===== حجر ورقة مقص (rps) =====

async def _show_rps_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()
    reward = await rps_queries.get_rps_reward(pool)

    text = gmessages.rps_settings_text(reward)
    keyboard = gkeyboards.rps_settings_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "owner:rps_reward")
async def rps_reward_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_rps_reward)
    await callback.message.edit_text(gmessages.REWARD_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_rps_reward)
async def rps_reward_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    reward = parse_number(message.text) if message.text else None

    if reward is None or reward <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await rps_queries.set_rps_reward(pool, reward)
    await state.clear()

    await message.reply(
        gmessages.rps_reward_updated_text(reward),
        reply_markup=gkeyboards.rps_settings_keyboard(),
    )


# ===== صندوق الحظ (lucky_box) =====

async def _show_lucky_box_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()
    fee = await lucky_box_queries.get_entry_fee(pool)
    outcomes = await lucky_box_queries.get_outcomes(pool)

    text = gmessages.lucky_box_settings_text(fee)
    keyboard = gkeyboards.lucky_box_settings_keyboard(outcomes)

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "owner:lucky_box_fee")
async def lucky_box_fee_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_lucky_box_fee)
    await callback.message.edit_text(gmessages.LUCKY_BOX_FEE_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_lucky_box_fee)
async def lucky_box_fee_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    fee = parse_number(message.text) if message.text else None

    if fee is None or fee <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await lucky_box_queries.set_entry_fee(pool, fee)
    await state.clear()

    outcomes = await lucky_box_queries.get_outcomes(pool)

    await message.reply(
        gmessages.lucky_box_fee_updated_text(fee),
        reply_markup=gkeyboards.lucky_box_settings_keyboard(outcomes),
    )


@router.callback_query(F.data.startswith("owner:lucky_box_remove:"))
async def lucky_box_remove(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    pool = await get_pool()
    outcomes = await lucky_box_queries.get_outcomes(pool)

    if len(outcomes) <= 1:
        await callback.answer(gmessages.LUCKY_BOX_MIN_OUTCOME, show_alert=True)
        return

    if 0 <= index < len(outcomes):
        outcomes.pop(index)
        await lucky_box_queries.set_outcomes(pool, outcomes)

    await _show_lucky_box_settings(callback)
    await callback.answer(gmessages.LUCKY_BOX_OUTCOME_REMOVED)


@router.callback_query(F.data == "owner:lucky_box_add")
async def lucky_box_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_lucky_box_outcome_amount)
    await callback.message.edit_text(gmessages.LUCKY_BOX_AMOUNT_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_lucky_box_outcome_amount)
async def lucky_box_amount_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    amount = parse_number(message.text) if message.text else None

    if amount is None or amount < 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    await state.update_data(new_outcome_amount=amount)
    await state.set_state(OwnerStates.waiting_lucky_box_outcome_weight)

    await message.reply(gmessages.LUCKY_BOX_WEIGHT_PROMPT, reply_markup=gkeyboards.cancel_keyboard())


@router.message(OwnerStates.waiting_lucky_box_outcome_weight)
async def lucky_box_weight_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    weight = parse_number(message.text) if message.text else None

    if weight is None or weight <= 0 or weight > 100:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    amount = data.get("new_outcome_amount")

    pool = await get_pool()
    outcomes = await lucky_box_queries.get_outcomes(pool)
    outcomes.append({"amount": amount, "weight": weight})
    await lucky_box_queries.set_outcomes(pool, outcomes)

    await state.clear()

    await message.reply(
        gmessages.lucky_box_outcome_added_text(amount, weight),
        reply_markup=gkeyboards.lucky_box_settings_keyboard(outcomes),
    )


# ===== الناجي الأخير (last_survivor) =====

async def _show_ls_settings(callback: CallbackQuery) -> None:
    pool = await get_pool()
    fee = await ls_queries.get_entry_fee(pool)
    join_window = await ls_queries.get_join_window(pool)
    min_players = await ls_queries.get_min_players(pool)
    elimination_delay = await ls_queries.get_elimination_delay(pool)

    text = gmessages.last_survivor_settings_text(fee, join_window, min_players, elimination_delay)
    keyboard = gkeyboards.last_survivor_settings_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)


async def _ls_refresh(message: Message) -> None:
    pool = await get_pool()
    fee = await ls_queries.get_entry_fee(pool)
    join_window = await ls_queries.get_join_window(pool)
    min_players = await ls_queries.get_min_players(pool)
    elimination_delay = await ls_queries.get_elimination_delay(pool)

    await message.reply(
        gmessages.ls_updated_text(fee, join_window, min_players, elimination_delay),
        reply_markup=gkeyboards.last_survivor_settings_keyboard(),
    )


@router.callback_query(F.data == "owner:ls_fee")
async def ls_fee_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_ls_fee)
    await callback.message.edit_text(gmessages.LS_FEE_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_ls_fee)
async def ls_fee_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await ls_queries.set_entry_fee(pool, value)
    await state.clear()

    await _ls_refresh(message)


@router.callback_query(F.data == "owner:ls_join_window")
async def ls_join_window_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_ls_join_window)
    await callback.message.edit_text(gmessages.LS_JOIN_WINDOW_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_ls_join_window)
async def ls_join_window_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await ls_queries.set_join_window(pool, value)
    await state.clear()

    await _ls_refresh(message)


@router.callback_query(F.data == "owner:ls_min_players")
async def ls_min_players_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_ls_min_players)
    await callback.message.edit_text(gmessages.LS_MIN_PLAYERS_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_ls_min_players)
async def ls_min_players_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value < 2:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await ls_queries.set_min_players(pool, value)
    await state.clear()

    await _ls_refresh(message)


@router.callback_query(F.data == "owner:ls_elimination_delay")
async def ls_elimination_delay_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_ls_elimination_delay)
    await callback.message.edit_text(gmessages.LS_ELIMINATION_DELAY_PROMPT, reply_markup=gkeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_ls_elimination_delay)
async def ls_elimination_delay_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(gmessages.INVALID_NUMBER, reply_markup=gkeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await ls_queries.set_elimination_delay(pool, value)
    await state.clear()

    await _ls_refresh(message)
