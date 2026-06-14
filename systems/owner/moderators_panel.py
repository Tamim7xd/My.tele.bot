"""
لوحة التحكم - نظام الإداريين (moderators).

يحتوي على:
- 👮 الإداريين: 🛡️ الأدمن (عدد) / 🔧 المشرفين (عدد)
- قائمة أعضاء برتبة معينة (6 لكل صفحة)
- صفحة عضو: ⬆️ ترقية / ⬇️ تخفيض / ⚙️ الصلاحيات
- صفحة الصلاحيات: تبديل ✅/❌ لكل صلاحية

هذا الملف يُسجَّل كجزء من router الرئيسي في owner.py عبر include_router.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner import keyboards
from systems.owner.notifications import messages
from systems.moderators import queries as moderators_queries
from systems.moderators import permissions
from systems.members import queries as members_queries


router = Router(name="owner_moderators")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id == OWNER_ID


# ===== القائمة الرئيسية (أدمن/مشرفين) =====

@router.callback_query(F.data == "owner:moderators")
async def show_moderators_main(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()

    admin_count = await moderators_queries.get_staff_count(pool, "admin")
    moderator_count = await moderators_queries.get_staff_count(pool, "moderator")

    text = messages.moderators_text(admin_count, moderator_count)
    keyboard = keyboards.moderators_main_keyboard(admin_count, moderator_count)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== قائمة أعضاء برتبة معينة =====

@router.callback_query(F.data.startswith("owner:mod_list:"))
async def show_staff_list(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, rank, offset_str = callback.data.split(":")
    offset = int(offset_str)

    pool = await get_pool()

    total = await moderators_queries.get_staff_count(pool, rank)
    staff = await moderators_queries.get_staff_list(pool, rank, offset=offset, limit=6)

    staff_data = [(m["user_id"], m["username"], m["full_name"]) for m in staff]

    text = messages.staff_list_text(rank, total)
    keyboard = keyboards.staff_list_keyboard(rank, staff_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== صفحة عضو إداري =====

@router.callback_query(F.data.startswith("owner:mod_member:"))
async def show_staff_member(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, rank, user_id_str, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    # الرتبة الفعلية الحالية (قد تكون تغيرت بعد ترقية/تخفيض)
    current_rank = member["rank"]

    text = messages.staff_member_text(member["full_name"], member["username"], current_rank)
    keyboard = keyboards.staff_member_keyboard(current_rank, user_id, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== الترقية =====

@router.callback_query(F.data.startswith("owner:mod_promote:"))
async def promote_member(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, old_rank, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    new_rank = await moderators_queries.promote(pool, user_id)

    member = await members_queries.get_member(pool, user_id)

    if member is None or new_rank is None:
        await callback.answer()
        return

    await callback.message.edit_text(
        messages.promoted_text(member["full_name"], new_rank),
        reply_markup=keyboards.staff_member_keyboard(new_rank, user_id, offset),
    )
    await callback.answer()


# ===== التخفيض =====

@router.callback_query(F.data.startswith("owner:mod_demote:"))
async def demote_member(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, old_rank, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    new_rank = await moderators_queries.demote(pool, user_id)

    member = await members_queries.get_member(pool, user_id)

    if member is None or new_rank is None:
        await callback.answer()
        return

    if new_rank == "member":
        # العضو أصبح "عضو" عادي - لا يظهر بعد الآن في قائمة admin/moderator
        await callback.message.edit_text(
            messages.demoted_text(member["full_name"], new_rank),
            reply_markup=keyboards.back_keyboard(),
        )
    else:
        await callback.message.edit_text(
            messages.demoted_text(member["full_name"], new_rank),
            reply_markup=keyboards.staff_member_keyboard(new_rank, user_id, offset),
        )

    await callback.answer()


# ===== الصلاحيات =====

@router.callback_query(F.data.startswith("owner:mod_perms:"))
async def show_permissions(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, rank, offset_str = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    current_rank = member["rank"]
    active_permissions = await permissions.get_permissions(pool, user_id)

    text = messages.permissions_text(member["full_name"], current_rank)
    keyboard = keyboards.permissions_keyboard(user_id, current_rank, offset, active_permissions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:mod_toggle_perm:"))
async def toggle_permission(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    _, _, user_id_str, rank, offset_str, perm_key = callback.data.split(":")
    user_id = int(user_id_str)
    offset = int(offset_str)

    pool = await get_pool()

    active_permissions = await permissions.get_permissions(pool, user_id)

    if perm_key in active_permissions:
        await moderators_queries.remove_permission(pool, user_id, perm_key)
    else:
        await moderators_queries.add_permission(pool, user_id, perm_key)

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer()
        return

    current_rank = member["rank"]
    updated_permissions = await permissions.get_permissions(pool, user_id)

    text = messages.permissions_text(member["full_name"], current_rank)
    keyboard = keyboards.permissions_keyboard(user_id, current_rank, offset, updated_permissions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
