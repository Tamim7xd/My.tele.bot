"""
لوحة التحكم - نظام المتجر (shop).

يحتوي على:
- 🛒 المتجر: العضويات / الألقاب / إعدادات مسح المحادثة / الأرشيف
- تعديل كامل لكل عضوية ولقب (اسم/سعر/مدة/مكافأة/مزايا)
- أرشيف: من اشترى كل عضوية + سجل مسح المحادثات لكل عضو

يُسجَّل كجزء من router الرئيسي عبر include_router في core/bot.py.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.owner.utils import parse_number
from systems.owner import shop_panel_keyboards as skeyboards
from systems.owner import shop_panel_messages as smessages
from systems.shop import queries as shop_queries
from systems.shop import member_queries as shop_member_queries


router = Router(name="owner_shop")


DURATION_UNIT_SECONDS = {
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
    "months": 2592000,
}


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== القائمة الرئيسية =====

@router.callback_query(F.data == "owner:shop")
async def show_shop_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    await callback.message.edit_text(smessages.SHOP_MAIN_TEXT, reply_markup=skeyboards.shop_main_keyboard())
    await callback.answer()


# ===== العضويات =====

@router.callback_query(F.data.startswith("owner:shop_memberships:"))
async def show_membership(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    memberships = await shop_queries.get_memberships(pool)

    if not memberships or not (0 <= index < len(memberships)):
        await callback.answer()
        return

    text = smessages.membership_admin_text(memberships[index])
    keyboard = skeyboards.memberships_list_keyboard(memberships, index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mship_edit_name:"))
async def membership_name_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    await state.set_state(OwnerStates.waiting_membership_name)
    await state.update_data(membership_id=membership_id)

    await callback.message.edit_text(smessages.NAME_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_membership_name)
async def membership_name_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    data = await state.get_data()
    membership_id = data.get("membership_id")

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await state.clear()
        return

    membership["name"] = message.text
    await shop_queries.update_membership(pool, membership_id, membership)
    await state.clear()

    await message.reply(
        smessages.updated_text("الاسم"),
        reply_markup=skeyboards.memberships_list_keyboard(await shop_queries.get_memberships(pool), 0),
    )


@router.callback_query(F.data.startswith("owner:mship_edit_price:"))
async def membership_price_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    await state.set_state(OwnerStates.waiting_membership_price)
    await state.update_data(membership_id=membership_id)

    await callback.message.edit_text(smessages.PRICE_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_membership_price)
async def membership_price_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    price = parse_number(message.text) if message.text else None

    if price is None or price < 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    membership_id = data.get("membership_id")

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await state.clear()
        return

    membership["price"] = price
    await shop_queries.update_membership(pool, membership_id, membership)
    await state.clear()

    await message.reply(
        smessages.updated_text("السعر"),
        reply_markup=skeyboards.memberships_list_keyboard(await shop_queries.get_memberships(pool), 0),
    )


@router.callback_query(F.data.startswith("owner:mship_edit_reward:"))
async def membership_reward_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    await state.set_state(OwnerStates.waiting_membership_daily_reward)
    await state.update_data(membership_id=membership_id)

    await callback.message.edit_text(smessages.REWARD_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_membership_daily_reward)
async def membership_reward_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    reward = parse_number(message.text) if message.text else None

    if reward is None or reward < 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    membership_id = data.get("membership_id")

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await state.clear()
        return

    membership["daily_reward"] = reward
    await shop_queries.update_membership(pool, membership_id, membership)
    await state.clear()

    await message.reply(
        smessages.updated_text("المكافأة اليومية"),
        reply_markup=skeyboards.memberships_list_keyboard(await shop_queries.get_memberships(pool), 0),
    )


# ===== تعديل المدة (وحدة + رقم) =====

@router.callback_query(F.data.startswith("owner:mship_edit_duration:"))
async def membership_duration_unit_prompt(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    await callback.message.edit_text(
        smessages.DURATION_VALUE_PROMPT,
        reply_markup=skeyboards.duration_unit_keyboard(membership_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mship_dur_permanent:"))
async def membership_duration_permanent(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    membership["duration_seconds"] = 0
    await shop_queries.update_membership(pool, membership_id, membership)

    memberships = await shop_queries.get_memberships(pool)
    index = next((i for i, m in enumerate(memberships) if m["id"] == membership_id), 0)

    await callback.message.edit_text(
        smessages.membership_admin_text(memberships[index]),
        reply_markup=skeyboards.memberships_list_keyboard(memberships, index),
    )
    await callback.answer(smessages.updated_text("المدة"))


@router.callback_query(F.data.startswith("owner:mship_dur_unit:"))
async def membership_duration_unit_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, membership_id, unit = callback.data.split(":")

    await state.set_state(OwnerStates.waiting_membership_duration_value)
    await state.update_data(membership_id=membership_id, duration_unit=unit)

    await callback.message.edit_text(smessages.DURATION_VALUE_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_membership_duration_value)
async def membership_duration_value_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    value = parse_number(message.text) if message.text else None

    if value is None or value <= 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    membership_id = data.get("membership_id")
    unit = data.get("duration_unit")

    seconds = value * DURATION_UNIT_SECONDS.get(unit, 86400)

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await state.clear()
        return

    membership["duration_seconds"] = seconds
    await shop_queries.update_membership(pool, membership_id, membership)
    await state.clear()

    memberships = await shop_queries.get_memberships(pool)
    index = next((i for i, m in enumerate(memberships) if m["id"] == membership_id), 0)

    await message.reply(
        smessages.updated_text("المدة"),
        reply_markup=skeyboards.memberships_list_keyboard(memberships, index),
    )


# ===== المزايا (toggle) =====

@router.callback_query(F.data.startswith("owner:mship_features:"))
async def membership_features(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    membership_id = callback.data.split(":")[-1]

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    text = smessages.membership_features_text(membership)
    keyboard = skeyboards.membership_features_keyboard(membership)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mship_toggle:"))
async def membership_toggle_feature(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, membership_id, feature_key = callback.data.split(":")

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    membership[feature_key] = not membership.get(feature_key, False)
    await shop_queries.update_membership(pool, membership_id, membership)

    text = smessages.membership_features_text(membership)
    keyboard = skeyboards.membership_features_keyboard(membership)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== من اشترى عضوية =====

@router.callback_query(F.data.startswith("owner:mship_owners:"))
async def show_membership_owners(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, membership_id, offset_str = callback.data.split(":")
    offset = int(offset_str)

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    total = await shop_member_queries.get_membership_owners_count(pool, membership_id)
    owners = await shop_member_queries.get_membership_owners(pool, membership_id, offset=offset, limit=5)

    text = smessages.owners_list_text(membership["name"], total, owners)
    keyboard = skeyboards.owners_list_keyboard(membership_id, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== الألقاب =====

@router.callback_query(F.data.startswith("owner:shop_titles:"))
async def show_title(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    titles = await shop_queries.get_titles(pool)

    if not titles or not (0 <= index < len(titles)):
        await callback.answer()
        return

    text = smessages.title_admin_text(titles[index])
    keyboard = skeyboards.titles_list_keyboard(titles, index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:title_edit_name:"))
async def title_name_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    title_id = callback.data.split(":")[-1]

    await state.set_state(OwnerStates.waiting_title_name)
    await state.update_data(title_id=title_id)

    await callback.message.edit_text(smessages.NAME_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_title_name)
async def title_name_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text:
        return

    data = await state.get_data()
    title_id = data.get("title_id")

    pool = await get_pool()
    title = await shop_queries.get_title_by_id(pool, title_id)

    if title is None:
        await state.clear()
        return

    title["name"] = message.text
    await shop_queries.update_title(pool, title_id, title)
    await state.clear()

    titles = await shop_queries.get_titles(pool)
    index = next((i for i, t in enumerate(titles) if t["id"] == title_id), 0)

    await message.reply(
        smessages.updated_text("الاسم"),
        reply_markup=skeyboards.titles_list_keyboard(titles, index),
    )


@router.callback_query(F.data.startswith("owner:title_edit_price:"))
async def title_price_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    title_id = callback.data.split(":")[-1]

    await state.set_state(OwnerStates.waiting_title_price)
    await state.update_data(title_id=title_id)

    await callback.message.edit_text(smessages.PRICE_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_title_price)
async def title_price_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    price = parse_number(message.text) if message.text else None

    if price is None or price < 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    title_id = data.get("title_id")

    pool = await get_pool()
    title = await shop_queries.get_title_by_id(pool, title_id)

    if title is None:
        await state.clear()
        return

    title["price"] = price
    await shop_queries.update_title(pool, title_id, title)
    await state.clear()

    titles = await shop_queries.get_titles(pool)
    index = next((i for i, t in enumerate(titles) if t["id"] == title_id), 0)

    await message.reply(
        smessages.updated_text("السعر"),
        reply_markup=skeyboards.titles_list_keyboard(titles, index),
    )


# ===== إعدادات مسح المحادثة =====

@router.callback_query(F.data == "owner:shop_clear_settings")
async def show_clear_settings(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    price = await shop_queries.get_clear_chat_price(pool)
    range_count = await shop_queries.get_clear_chat_range(pool)

    text = smessages.clear_settings_text(price, range_count)
    keyboard = skeyboards.clear_settings_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "owner:shop_clear_price")
async def clear_price_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_clear_chat_price)
    await callback.message.edit_text(smessages.CLEAR_PRICE_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_clear_chat_price)
async def clear_price_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    price = parse_number(message.text) if message.text else None

    if price is None or price < 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await shop_queries.set_clear_chat_price(pool, price)
    await state.clear()

    range_count = await shop_queries.get_clear_chat_range(pool)

    await message.reply(
        smessages.clear_settings_text(price, range_count),
        reply_markup=skeyboards.clear_settings_keyboard(),
    )


@router.callback_query(F.data == "owner:shop_clear_range")
async def clear_range_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_clear_chat_range)
    await callback.message.edit_text(smessages.CLEAR_RANGE_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_clear_chat_range)
async def clear_range_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    range_count = parse_number(message.text) if message.text else None

    if range_count is None or range_count <= 0:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    pool = await get_pool()
    await shop_queries.set_clear_chat_range(pool, range_count)
    await state.clear()

    price = await shop_queries.get_clear_chat_price(pool)

    await message.reply(
        smessages.clear_settings_text(price, range_count),
        reply_markup=skeyboards.clear_settings_keyboard(),
    )


# ===== الأرشيف =====

@router.callback_query(F.data == "owner:shop_archive")
async def show_archive(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text(smessages.ARCHIVE_MAIN_TEXT, reply_markup=skeyboards.archive_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("owner:shop_clear_archive:"))
async def show_clear_archive_list(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    pool = await get_pool()
    total = await shop_member_queries.get_members_with_clear_history_count(pool)
    members = await shop_member_queries.get_members_with_clear_history(pool, offset=offset, limit=6)

    members_data = [(m["user_id"], m["username"], m["full_name"], m["clear_count"]) for m in members]

    text = smessages.clear_archive_list_text(total)
    keyboard = skeyboards.clear_archive_list_keyboard(members_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:shop_clear_member:"))
async def show_clear_member_history(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, page_str = callback.data.split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    pool = await get_pool()

    from systems.members import queries as members_queries
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    total = await shop_member_queries.get_clear_chat_history_count(pool, user_id)
    entries = await shop_member_queries.get_clear_chat_history(pool, user_id, offset=page * 5, limit=5)

    text = smessages.clear_member_history_text(member["full_name"], entries, total)
    keyboard = skeyboards.clear_member_history_keyboard(user_id, page, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== إدارة عضوية عضو من صفحته (👥 الأعضاء) =====

async def _render_member_membership(callback: CallbackQuery, user_id: int, offset: int) -> None:
    from systems.members import queries as members_queries

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    membership_info = await shop_member_queries.get_member_full_membership_info(pool, user_id)

    text = smessages.member_membership_text(member["full_name"], membership_info)
    has_membership = membership_info is not None
    keyboard = skeyboards.member_membership_keyboard(user_id, offset, has_membership)

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:member_mship:"))
async def show_member_membership(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await _render_member_membership(callback, user_id, offset)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mship_revoke:"))
async def revoke_member_membership(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    await shop_member_queries.revoke_membership(pool, user_id)

    await callback.answer(smessages.MEMBERSHIP_REVOKED, show_alert=True)
    await _render_member_membership(callback, user_id, offset)


@router.callback_query(F.data.startswith("owner:mship_extend:"))
async def extend_member_membership_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    membership_info = await shop_member_queries.get_member_full_membership_info(pool, user_id)

    if membership_info is None:
        await callback.answer(smessages.NO_ACTIVE_MEMBERSHIP_TO_EXTEND, show_alert=True)
        return

    await state.set_state(OwnerStates.waiting_member_membership_extend)
    await state.update_data(target_user_id=user_id, offset=offset)

    await callback.message.edit_text(smessages.MEMBERSHIP_EXTEND_PROMPT, reply_markup=skeyboards.cancel_keyboard())
    await callback.answer()


@router.message(OwnerStates.waiting_member_membership_extend)
async def extend_member_membership_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    days = parse_number(message.text) if message.text else None

    if days is None:
        await message.reply(smessages.INVALID_NUMBER, reply_markup=skeyboards.cancel_keyboard())
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")
    offset = data.get("offset", 0)

    pool = await get_pool()
    new_expires = await shop_member_queries.extend_membership(pool, user_id, days * 86400)
    await state.clear()

    if new_expires is None:
        await message.reply(smessages.NO_ACTIVE_MEMBERSHIP_TO_EXTEND)
        return

    expires_str = new_expires.strftime("%Y-%m-%d %H:%M")

    from systems.members import queries as members_queries
    member = await members_queries.get_member(pool, user_id)
    membership_info = await shop_member_queries.get_member_full_membership_info(pool, user_id)

    await message.reply(
        smessages.membership_extended_text(expires_str),
        reply_markup=skeyboards.member_membership_keyboard(user_id, offset, membership_info is not None),
    )


# ===== منح عضوية مباشرة (بدون دفع) من اللوحة =====

@router.callback_query(F.data.startswith("owner:mship_grant:"))
async def grant_membership_browse(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, index_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    index = int(index_str)

    pool = await get_pool()
    memberships = await shop_queries.get_memberships(pool)

    if not memberships or not (0 <= index < len(memberships)):
        await callback.answer()
        return

    text = smessages.membership_admin_text(memberships[index])
    keyboard = skeyboards.grant_membership_keyboard(user_id, offset, memberships, index)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mship_grant_confirm:"))
async def grant_membership_confirm(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, membership_id = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    membership = await shop_queries.get_membership_by_id(pool, membership_id)

    if membership is None:
        await callback.answer()
        return

    await shop_member_queries.set_member_membership(pool, user_id, membership_id, membership["duration_seconds"])
    await shop_member_queries.log_purchase(pool, user_id, "membership", membership_id, 0)

    await callback.answer(smessages.updated_text("العضوية"), show_alert=True)
    await _render_member_membership(callback, user_id, offset)
