"""
لوحة التحكم - نظام الأعضاء (members).

يحتوي على:
- 👥 الأعضاء: قائمة جميع الأعضاء (6 لكل صفحة) + 🔍 بحث
- صفحة عضو: عرض بياناته الكاملة + 💰 تعديل الرصيد
- تعديل الرصيد: أزرار سريعة (+/- 1,000/5,000/10,000) + تحديد قيمة مخصصة

هذا الملف يُسجَّل كجزء من router الرئيسي في owner.py عبر include_router،
ويستخدم نفس فحص _is_owner.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.states import OwnerStates
from systems.owner.notifications import messages
from systems.owner.utils import parse_number
from systems.members import queries as members_queries
from systems.moderators import queries as moderators_queries
from systems.wallet import wallet


router = Router(name="owner_members")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== قائمة الأعضاء =====

@router.callback_query(F.data.startswith("owner:members:"))
async def show_members_list(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    await state.clear()

    pool = await get_pool()
    total = await members_queries.get_members_count(pool)
    members = await members_queries.get_all_members(pool, offset=offset, limit=6)

    members_data = [(m["user_id"], m["username"], m["full_name"]) for m in members]

    text = messages.members_list_text(total)
    keyboard = keyboards.members_list_keyboard(members_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== البحث =====

@router.callback_query(F.data == "owner:member_search")
async def member_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_member_search)

    await callback.message.edit_text(
        messages.MEMBER_SEARCH_PROMPT,
        reply_markup=keyboards.search_cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_member_search)
async def member_search_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None:
        return

    pool = await get_pool()
    results = await members_queries.search_member(pool, message.text.strip())

    await state.clear()

    if not results:
        await message.reply(
            messages.MEMBER_SEARCH_NO_RESULTS,
            reply_markup=keyboards.search_cancel_keyboard(),
        )
        return

    results_data = [(m["user_id"], m["username"], m["full_name"]) for m in results]

    await message.reply(
        "🔍 نتائج البحث:",
        reply_markup=keyboards.search_results_keyboard(results_data),
    )


# ===== صفحة عضو =====

@router.callback_query(F.data.startswith("owner:member:"))
async def show_member_page(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await state.clear()

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.member_page_text(
        full_name=member["full_name"],
        username=member["username"],
        rank=member["rank"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        is_muted=member["is_muted"],
        is_banned=member["is_banned"],
    )

    keyboard = keyboards.member_page_keyboard(
        user_id, offset, member["rank"],
        is_muted=member["is_muted"], is_banned=member["is_banned"],
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== تعديل الرصيد =====

@router.callback_query(F.data.startswith("owner:member_balance:"))
async def show_balance_edit(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await state.clear()

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.balance_edit_text(member["full_name"], member["balance"])
    keyboard = keyboards.balance_edit_keyboard(user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:bal_add:"))
async def balance_quick_add(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, amount_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    amount = int(amount_str)

    pool = await get_pool()
    await wallet.add_balance(pool, user_id, amount)

    await _refresh_balance_edit(callback, user_id, offset)


@router.callback_query(F.data.startswith("owner:bal_sub:"))
async def balance_quick_sub(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, amount_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    amount = int(amount_str)

    pool = await get_pool()
    current = await wallet.get_balance(pool, user_id)
    new_value = max(0, current - amount)
    await wallet.set_balance(pool, user_id, new_value)

    await _refresh_balance_edit(callback, user_id, offset)


async def _refresh_balance_edit(callback: CallbackQuery, user_id: int, offset: int) -> None:
    """يعيد عرض صفحة تعديل الرصيد بالقيمة الجديدة."""
    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.balance_edit_text(member["full_name"], member["balance"])
    keyboard = keyboards.balance_edit_keyboard(user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:bal_custom:"))
async def balance_custom_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await state.set_state(OwnerStates.waiting_member_balance)
    await state.update_data(target_user_id=user_id, offset=offset)

    await callback.message.edit_text(
        messages.BALANCE_CUSTOM_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_member_balance)
async def balance_custom_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    new_balance = parse_number(message.text) if message.text else None

    if new_balance is None:
        await message.reply(
            messages.BALANCE_CUSTOM_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")
    offset = data.get("offset", 0)

    if user_id is None:
        await state.clear()
        return

    pool = await get_pool()
    await wallet.set_balance(pool, user_id, new_balance)

    member = await members_queries.get_member(pool, user_id)

    await state.clear()

    await message.reply(
        messages.balance_updated_text(member["full_name"], new_balance),
        reply_markup=keyboards.member_page_keyboard(
            user_id, offset, member["rank"],
            is_muted=member["is_muted"], is_banned=member["is_banned"],
        ),
    )


# ===== تعديل المستوى =====

@router.callback_query(F.data.startswith("owner:member_level:"))
async def show_level_edit(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await state.clear()

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.level_edit_text(member["full_name"], member["level"])
    keyboard = keyboards.level_edit_keyboard(user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:lvl_add:"))
async def level_quick_add(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, amount_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    amount = int(amount_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    new_level = member["level"] + amount
    await members_queries.set_level(pool, user_id, new_level)

    await _refresh_level_edit(callback, user_id, offset)


@router.callback_query(F.data.startswith("owner:lvl_sub:"))
async def level_quick_sub(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str, amount_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)
    amount = int(amount_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    new_level = max(1, member["level"] - amount)
    await members_queries.set_level(pool, user_id, new_level)

    await _refresh_level_edit(callback, user_id, offset)


async def _refresh_level_edit(callback: CallbackQuery, user_id: int, offset: int) -> None:
    """يعيد عرض صفحة تعديل المستوى بالقيمة الجديدة."""
    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    text = messages.level_edit_text(member["full_name"], member["level"])
    keyboard = keyboards.level_edit_keyboard(user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:lvl_custom:"))
async def level_custom_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    await state.set_state(OwnerStates.waiting_member_level)
    await state.update_data(target_user_id=user_id, offset=offset)

    await callback.message.edit_text(
        messages.LEVEL_CUSTOM_PROMPT,
        reply_markup=keyboards.cancel_edit_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_member_level)
async def level_custom_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    new_level = parse_number(message.text) if message.text else None

    if new_level is None or new_level < 1:
        await message.reply(
            messages.LEVEL_CUSTOM_INVALID,
            reply_markup=keyboards.cancel_edit_keyboard(),
        )
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")
    offset = data.get("offset", 0)

    if user_id is None:
        await state.clear()
        return

    pool = await get_pool()
    await members_queries.set_level(pool, user_id, new_level)

    member = await members_queries.get_member(pool, user_id)

    await state.clear()

    await message.reply(
        messages.level_updated_text(member["full_name"], new_level),
        reply_markup=keyboards.member_page_keyboard(
            user_id, offset, member["rank"],
            is_muted=member["is_muted"], is_banned=member["is_banned"],
        ),
    )


# ===== الترقية / التخفيض من صفحة العضو =====

@router.callback_query(F.data.startswith("owner:member_promote:"))
async def member_promote(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    new_rank = await moderators_queries.promote(pool, user_id)
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    if new_rank is None:
        await callback.answer("❌ لا يمكن الترقية أكثر.", show_alert=True)
        return

    text = messages.member_page_text(
        full_name=member["full_name"],
        username=member["username"],
        rank=member["rank"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        is_muted=member["is_muted"],
        is_banned=member["is_banned"],
    )

    keyboard = keyboards.member_page_keyboard(
        user_id, offset, member["rank"],
        is_muted=member["is_muted"], is_banned=member["is_banned"],
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.promoted_text(member["full_name"], new_rank))


@router.callback_query(F.data.startswith("owner:member_demote:"))
async def member_demote(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    new_rank = await moderators_queries.demote(pool, user_id)
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    if new_rank is None:
        await callback.answer("❌ لا يمكن التخفيض أكثر.", show_alert=True)
        return

    text = messages.member_page_text(
        full_name=member["full_name"],
        username=member["username"],
        rank=member["rank"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        is_muted=member["is_muted"],
        is_banned=member["is_banned"],
    )

    keyboard = keyboards.member_page_keyboard(
        user_id, offset, member["rank"],
        is_muted=member["is_muted"], is_banned=member["is_banned"],
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.demoted_text(member["full_name"], new_rank))
