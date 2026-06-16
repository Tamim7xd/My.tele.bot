"""
نظام إدارة العضويات الإدارية.
يعمل بنفس أسلوب المشروع: owner:action callback_data.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database import (
    get_pool, get_ranks, get_rank_by_id, get_rank_by_name,
    add_rank, update_rank, delete_rank,
    get_rank_permissions, set_rank_permissions,
    get_permissions_list, get_permission_by_code
)
from systems.owner.states import OwnerStates
from systems.owner.notifications import messages as msg
from systems.owner.utils import owner_only

router = Router()


# ═══════════════════════════════════════
# الزر الرئيسي - فتح لوحة العضويات
# ═══════════════════════════════════════
@router.callback_query(F.data == "owner:ranks")
@owner_only
async def ranks_main(callback: CallbackQuery):
    """القائمة الرئيسية لنظام العضويات"""
    pool = await get_pool()
    ranks = await get_ranks(pool)
    
    text = msg.ranks_main_text(ranks)
    keyboard = msg.ranks_main_keyboard(ranks)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════
# عرض تفاصيل عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("owner:rank:view:"))
@owner_only
async def rank_view(callback: CallbackQuery):
    """عرض تفاصيل عضوية معينة"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if not rank:
        await callback.answer("❌ العضوية غير موجودة!")
        return
    
    all_perms = await get_permissions_list(pool)
    rank_perms = rank['permissions'] or []
    
    text = msg.rank_details_text(rank, all_perms, rank_perms)
    keyboard = msg.rank_details_keyboard(rank)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


# ═══════════════════════════════════════
# بدء إضافة عضوية جديدة
# ═══════════════════════════════════════
@router.callback_query(F.data == "owner:rank:add")
@owner_only
async def rank_add_start(callback: CallbackQuery, state: FSMContext):
    """بدء إضافة عضوية جديدة"""
    await state.set_state(OwnerStates.waiting_rank_name)
    await callback.message.edit_text(
        msg.RANK_ADD_NAME_PROMPT,
        reply_markup=msg.cancel_keyboard()
    )


@router.message(OwnerStates.waiting_rank_name)
@owner_only
async def rank_add_name(message: Message, state: FSMContext):
    """الاسم التقني للعضوية"""
    name = message.text.strip().lower().replace(" ", "_")
    
    if not all(c.isalnum() or c == '_' for c in name):
        await message.answer(msg.RANK_ADD_NAME_INVALID)
        return
    
    pool = await get_pool()
    existing = await get_rank_by_name(pool, name)
    if existing:
        await message.answer(msg.RANK_ADD_NAME_EXISTS)
        return
    
    await state.update_data(rank_name=name)
    await state.set_state(OwnerStates.waiting_rank_display)
    
    await message.answer(
        msg.RANK_ADD_DISPLAY_PROMPT,
        reply_markup=msg.cancel_keyboard()
    )


@router.message(OwnerStates.waiting_rank_display)
@owner_only
async def rank_add_display(message: Message, state: FSMContext):
    """الاسم المعروض للعضوية"""
    await state.update_data(rank_display=message.text.strip())
    await state.set_state(OwnerStates.waiting_rank_level)
    
    pool = await get_pool()
    ranks = await get_ranks(pool)
    
    text = msg.rank_add_level_prompt(ranks)
    await message.answer(text, reply_markup=msg.cancel_keyboard())


@router.message(OwnerStates.waiting_rank_level)
@owner_only
async def rank_add_level(message: Message, state: FSMContext):
    """المستوى الهرمي"""
    try:
        level = int(message.text.strip())
        if level < 1 or level > 100:
            raise ValueError
    except ValueError:
        await message.answer(msg.RANK_ADD_LEVEL_INVALID)
        return
    
    pool = await get_pool()
    ranks = await get_ranks(pool)
    existing_levels = [r['level'] for r in ranks]
    
    if level in existing_levels:
        await message.answer(
            msg.rank_add_level_exists(level, existing_levels)
        )
        return
    
    await state.update_data(rank_level=level)
    
    await message.answer(
        msg.RANK_ADD_COLOR_PROMPT,
        reply_markup=msg.colors_keyboard()
    )


@router.callback_query(F.data.startswith("owner:rank:color:"))
@owner_only
async def rank_add_color(callback: CallbackQuery, state: FSMContext):
    """اختيار اللون"""
    color = callback.data.split(":")[3]
    await state.update_data(rank_color=color)
    await state.set_state(OwnerStates.waiting_rank_icon)
    
    await callback.message.edit_text(
        msg.RANK_ADD_ICON_PROMPT,
        reply_markup=msg.icons_keyboard()
    )


@router.message(OwnerStates.waiting_rank_icon)
@owner_only
async def rank_add_icon(message: Message, state: FSMContext):
    """الأيقونة"""
    icon = message.text.strip()
    if len(icon) > 5:
        await message.answer(msg.RANK_ADD_ICON_INVALID)
        return
    
    data = await state.get_data()
    pool = await get_pool()
    
    # إنشاء العضوية بدون صلاحيات
    rank_id = await add_rank(
        pool,
        name=data['rank_name'],
        display_name=data['rank_display'],
        level=data['rank_level'],
        color=data['rank_color'],
        icon=icon,
        permissions=[],
        created_by=message.from_user.id
    )
    
    await state.clear()
    
    # الانتقال لاختيار الصلاحيات
    all_perms = await get_permissions_list(pool)
    await message.answer(
        msg.rank_add_permissions_text(data['rank_display']),
        reply_markup=msg.permissions_selector_keyboard(rank_id, [], all_perms)
    )


# ═══════════════════════════════════════
# تعديل عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("owner:rank:edit:"))
@owner_only
async def rank_edit_menu(callback: CallbackQuery):
    """قائمة تعديل عضوية"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if not rank:
        await callback.answer("❌ غير موجودة!")
        return
    
    if rank['is_protected']:
        await callback.answer("🔒 محمية!")
        return
    
    text = msg.rank_edit_text(rank)
    keyboard = msg.rank_edit_keyboard(rank_id)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:rank:edit_name:"))
@owner_only
async def rank_edit_name_start(callback: CallbackQuery, state: FSMContext):
    """بدء تعديل الاسم"""
    rank_id = int(callback.data.split(":")[3])
    await state.update_data(edit_rank_id=rank_id)
    await state.set_state(OwnerStates.waiting_rank_edit_name)
    
    await callback.message.edit_text(
        msg.RANK_EDIT_NAME_PROMPT,
        reply_markup=msg.cancel_keyboard()
    )


@router.message(OwnerStates.waiting_rank_edit_name)
@owner_only
async def rank_edit_name_save(message: Message, state: FSMContext):
    """حفظ الاسم الجديد"""
    data = await state.get_data()
    rank_id = data['edit_rank_id']
    new_name = message.text.strip()
    
    pool = await get_pool()
    await update_rank(pool, rank_id, display_name=new_name)
    
    await state.clear()
    await message.answer(msg.RANK_EDIT_NAME_SUCCESS)
    
    # إعادة عرض التفاصيل
    rank = await get_rank_by_id(pool, rank_id)
    all_perms = await get_permissions_list(pool)
    rank_perms = rank['permissions'] or []
    
    await message.answer(
        msg.rank_details_text(rank, all_perms, rank_perms),
        reply_markup=msg.rank_details_keyboard(rank)
    )


# ═══════════════════════════════════════
# إدارة الصلاحيات
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("owner:rank:perms:"))
@owner_only
async def rank_permissions(callback: CallbackQuery):
    """عرض صلاحيات عضوية"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if rank['is_protected']:
        await callback.answer("🔒 محمية!")
        return
    
    current_perms = await get_rank_permissions(pool, rank_id)
    all_perms = await get_permissions_list(pool)
    
    text = msg.rank_permissions_text(rank, current_perms)
    keyboard = msg.permissions_selector_keyboard(rank_id, current_perms, all_perms)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:rank:toggle_perm:"))
@owner_only
async def rank_toggle_permission(callback: CallbackQuery):
    """تفعيل/تعطيل صلاحية"""
    parts = callback.data.split(":")
    rank_id = int(parts[3])
    perm_code = parts[4]
    
    pool = await get_pool()
    current_perms = await get_rank_permissions(pool, rank_id)
    
    if perm_code in current_perms:
        current_perms.remove(perm_code)
        action = "إزالة"
    else:
        current_perms.append(perm_code)
        action = "إضافة"
    
    await set_rank_permissions(pool, rank_id, current_perms)
    
    # تحديث العرض
    all_perms = await get_permissions_list(pool)
    rank = await get_rank_by_id(pool, rank_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=msg.permissions_selector_keyboard(rank_id, current_perms, all_perms)
    )
    await callback.answer(f"✅ تم {action}")


@router.callback_query(F.data.startswith("owner:rank:save_perms:"))
@owner_only
async def rank_save_permissions(callback: CallbackQuery):
    """حفظ الصلاحيات"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    perms = await get_rank_permissions(pool, rank_id)
    
    await callback.message.edit_text(
        msg.rank_permissions_saved(rank, perms),
        reply_markup=msg.back_to_rank_keyboard(rank_id)
    )


# ═══════════════════════════════════════
# حذف عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("owner:rank:delete:"))
@owner_only
async def rank_delete_confirm(callback: CallbackQuery):
    """تأكيد حذف عضوية"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if rank['is_protected']:
        await callback.answer("🔒 لا يمكن حذف العضوية المحمية!")
        return
    
    text = msg.rank_delete_confirm_text(rank)
    keyboard = msg.rank_delete_confirm_keyboard(rank_id)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("owner:rank:confirm_delete:"))
@owner_only
async def rank_delete_execute(callback: CallbackQuery):
    """تنفيذ الحذف"""
    rank_id = int(callback.data.split(":")[3])
    pool = await get_pool()
    
    # نقل الأعضاء للعضوية العادية (المستوى 4 = member)
    await pool.execute("""
        UPDATE members SET rank_id = 4 WHERE rank_id = $1
    """, rank_id)
    
    # حذف العضوية
    deleted = await delete_rank(pool, rank_id)
    
    if deleted:
        await callback.message.edit_text(
            msg.RANK_DELETE_SUCCESS,
            reply_markup=msg.back_to_ranks_keyboard()
        )
    else:
        await callback.answer("❌ فشل الحذف!")


# ═══════════════════════════════════════
# إشعارات المجموعة
# ═══════════════════════════════════════
async def notify_group_rank_change(bot, group_id: int, user_id: int, 
                                    old_rank: str, new_rank: str, 
                                    action: str = "promoted"):
    """إرسال إشعار للمجموعة عن تغيير العضوية"""
    from core.notifier import send_group_notification
    
    if action == "promoted":
        text = msg.group_promoted_text(user_id, old_rank, new_rank)
    elif action == "demoted":
        text = msg.group_demoted_text(user_id, old_rank, new_rank)
    else:
        text = msg.group_rank_changed_text(user_id, old_rank, new_rank)
    
    await send_group_notification(bot, group_id, text, pin=True)
