"""
لوحة إدارة العضويات الإدارية
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database import (
    get_pool, get_ranks, get_rank_by_id, get_rank_by_name,
    add_rank, update_rank, delete_rank,
    get_rank_permissions, set_rank_permissions,
    get_permissions_list
)
from systems.owner.utils import owner_only
from systems.owner.keyboards import (
    ranks_list_keyboard, rank_details_keyboard,
    permissions_selector_keyboard, colors_keyboard,
    icons_keyboard, cancel_keyboard, back_keyboard,
    edit_rank_keyboard, confirm_delete_keyboard
)

router = Router()

class RankStates(StatesGroup):
    creating_name = State()
    creating_display = State()
    creating_level = State()
    creating_color = State()
    creating_icon = State()
    editing_name = State()


# ═══════════════════════════════════════
# عرض قائمة العضويات
# ═══════════════════════════════════════
@router.callback_query(F.data == "ranks_panel")
@owner_only
async def show_ranks_panel(callback: CallbackQuery):
    pool = await get_pool()
    ranks = await get_ranks(pool)
    
    text = "👑 <b>إدارة العضويات الإدارية</b>\n\n"
    text += "📊 <b>الترتيب الهرمي:</b> (الرقم الأصغر = أعلى صلاحية)\n"
    
    for rank in ranks:
        protected = "🔒" if rank['is_protected'] else ""
        perms_count = len(rank['permissions']) if rank['permissions'] else 0
        text += f"\n{rank['icon']} <b>{rank['display_name']}</b> {protected}\n"
        text += f"├ المستوى: {rank['level']}\n"
        text += f"├ الصلاحيات: {perms_count}\n"
        text += f"└ اللون: <code>{rank['color']}</code>\n"
    
    await callback.message.edit_text(text, reply_markup=ranks_list_keyboard(ranks))


# ═══════════════════════════════════════
# عرض تفاصيل عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("view_rank:"))
@owner_only
async def view_rank_details(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if not rank:
        await callback.answer("❌ العضوية غير موجودة!")
        return
    
    all_perms = await get_permissions_list(pool)
    rank_perms = rank['permissions'] or []
    
    categories = {}
    for perm in all_perms:
        cat = perm['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(perm)
    
    cat_names = {
        'moderation': '🛡️ الإشراف',
        'systems': '⚙️ الأنظمة',
        'admin': '⚙️ الإدارة',
        'economy': '💰 الاقتصاد',
        'content': '📝 المحتوى',
        'special': '⭐ خاص'
    }
    
    text = f"{rank['icon']} <b>{rank['display_name']}</b>\n\n"
    text += f"📋 <b>المعلومات:</b>\n"
    text += f"├ الاسم التقني: <code>{rank['name']}</code>\n"
    text += f"├ المستوى: {rank['level']}\n"
    text += f"├ اللون: <code>{rank['color']}</code>\n"
    text += f"├ الأيقونة: {rank['icon']}\n"
    text += f"└ محمية: {'نعم 🔒' if rank['is_protected'] else 'لا'}\n\n"
    
    text += f"⚡ <b>الصلاحيات ({len(rank_perms)}):</b>\n"
    for cat_name, perms in categories.items():
        cat_perms = [p for p in perms if p['code'] in rank_perms]
        if cat_perms:
            emoji = cat_names.get(cat_name, '📌')
            text += f"\n{emoji} <b>{cat_name.upper()}:</b>\n"
            for perm in cat_perms:
                text += f"  ✓ {perm['icon']} {perm['display_name']}\n"
    
    await callback.message.edit_text(
        text, reply_markup=rank_details_keyboard(rank)
    )


# ═══════════════════════════════════════
# إضافة عضوية جديدة
# ═══════════════════════════════════════
@router.callback_query(F.data == "add_rank")
@owner_only
async def start_add_rank(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RankStates.creating_name)
    await callback.message.edit_text(
        "➕ <b>إضافة عضوية إدارية جديدة</b>\n\n"
        "📝 <b>الخطوة 1/5:</b> أرسل الاسم التقني (بالإنجليزية)\n"
        "مثال: <code>super_mod</code> أو <code>helper</code>\n\n"
        "⚠️ هذا الاسم يُستخدم داخلياً ولا يُعرض للأعضاء.",
        reply_markup=cancel_keyboard()
    )


@router.message(RankStates.creating_name)
@owner_only
async def process_rank_name(message: Message, state: FSMContext):
    name = message.text.strip().lower().replace(" ", "_")
    
    if not all(c.isalnum() or c == '_' for c in name):
        await message.answer("❌ الاسم يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط")
        return
    
    pool = await get_pool()
    existing = await get_rank_by_name(pool, name)
    if existing:
        await message.answer("❌ هذا الاسم مستخدم بالفعل!")
        return
    
    await state.update_data(rank_name=name)
    await state.set_state(RankStates.creating_display)
    
    await message.answer(
        "✅ تم حفظ الاسم التقني\n\n"
        "📝 <b>الخطوة 2/5:</b> أرسل الاسم المعروض (بالعربية)\n"
        "مثال: <code>🌟 المساعد المميز</code>",
        reply_markup=cancel_keyboard()
    )


@router.message(RankStates.creating_display)
@owner_only
async def process_rank_display(message: Message, state: FSMContext):
    await state.update_data(display_name=message.text.strip())
    await state.set_state(RankStates.creating_level)
    
    pool = await get_pool()
    ranks = await get_ranks(pool)
    
    text = "📊 <b>الخطوة 3/5:</b> اختر المستوى الهرمي\n\n"
    text += "🔢 <b>المستويات الحالية:</b>\n"
    for r in ranks:
        text += f"  المستوى {r['level']}: {r['display_name']}\n"
    
    text += "\n✏️ أرسل رقم المستوى الجديد (1-100):\n"
    text += "💡 <b>ملاحظة:</b> الرقم الأصغر = أعلى صلاحية"
    
    await message.answer(text, reply_markup=cancel_keyboard())


@router.message(RankStates.creating_level)
@owner_only
async def process_rank_level(message: Message, state: FSMContext):
    try:
        level = int(message.text.strip())
        if level < 1 or level > 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ أرسل رقم صحيح بين 1 و 100")
        return
    
    pool = await get_pool()
    ranks = await get_ranks(pool)
    existing_levels = [r['level'] for r in ranks]
    
    if level in existing_levels:
        available = [l for l in range(1, 101) if l not in existing_levels][:15]
        await message.answer(
            f"⚠️ المستوى {level} مستخدم!\n"
            f"المستويات المتاحة: {available}\n"
            f"أرسل مستوى آخر:"
        )
        return
    
    await state.update_data(level=level)
    
    await message.answer(
        "🎨 <b>الخطوة 4/5:</b> اختر لون العضوية\n\n"
        "أرسل كود HEX أو اختر من القائمة:",
        reply_markup=colors_keyboard()
    )


@router.callback_query(F.data.startswith("color:"))
@owner_only
async def select_color(callback: CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(RankStates.creating_icon)
    
    await callback.message.edit_text(
        "🎯 <b>الخطوة 5/5:</b> اختر أيقونة العضوية\n\n"
        "أرسل إيموجي واحد:",
        reply_markup=icons_keyboard()
    )


@router.message(RankStates.creating_icon)
@owner_only
async def process_rank_icon(message: Message, state: FSMContext):
    icon = message.text.strip()
    if len(icon) > 5:
        await message.answer("❌ أرسل إيموجي واحد فقط!")
        return
    
    data = await state.get_data()
    pool = await get_pool()
    
    rank_id = await add_rank(
        pool,
        name=data['rank_name'],
        display_name=data['display_name'],
        level=data['level'],
        color=data['color'],
        icon=icon,
        permissions=[],
        created_by=message.from_user.id
    )
    
    await state.clear()
    
    all_perms = await get_permissions_list(pool)
    await message.answer(
        f"✅ <b>تم إنشاء العضوية!</b>\n\n"
        f"{icon} <b>{data['display_name']}</b>\n"
        f"الآن اختر الصلاحيات:",
        reply_markup=permissions_selector_keyboard(rank_id, [], all_perms)
    )


# ═══════════════════════════════════════
# تعديل عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("edit_rank:"))
@owner_only
async def edit_rank_menu(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if not rank:
        await callback.answer("❌ غير موجودة!")
        return
    
    if rank['is_protected']:
        await callback.answer("🔒 هذه العضوية محمية!")
        return
    
    await callback.message.edit_text(
        f"✏️ <b>تعديل: {rank['display_name']}</b>\n\n"
        f"اختر ما تريد تعديله:",
        reply_markup=edit_rank_keyboard(rank_id)
    )


@router.callback_query(F.data.startswith("change_name:"))
@owner_only
async def start_change_name(callback: CallbackQuery, state: FSMContext):
    rank_id = int(callback.data.split(":")[1])
    await state.update_data(edit_rank_id=rank_id)
    await state.set_state(RankStates.editing_name)
    
    await callback.message.edit_text(
        "✏️ <b>تغيير الاسم المعروض</b>\n\n"
        "أرسل الاسم الجديد:",
        reply_markup=cancel_keyboard()
    )


@router.message(RankStates.editing_name)
@owner_only
async def save_rank_name(message: Message, state: FSMContext):
    data = await state.get_data()
    rank_id = data['edit_rank_id']
    new_name = message.text.strip()
    
    pool = await get_pool()
    await update_rank(pool, rank_id, display_name=new_name)
    
    await state.clear()
    await message.answer(f"✅ تم التحديث!")
    
    rank = await get_rank_by_id(pool, rank_id)
    await message.answer(
        f"{rank['icon']} <b>{rank['display_name']}</b>\n\nتم التحديث بنجاح!",
        reply_markup=back_keyboard("ranks_panel")
    )


# ═══════════════════════════════════════
# إدارة الصلاحيات
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("manage_perms:"))
@owner_only
async def manage_permissions(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if rank['is_protected']:
        await callback.answer("🔒 محمية!")
        return
    
    current_perms = await get_rank_permissions(pool, rank_id)
    all_perms = await get_permissions_list(pool)
    
    await callback.message.edit_text(
        f"⚡ <b>صلاحيات: {rank['display_name']}</b>\n\n"
        f"اختر الصلاحيات:",
        reply_markup=permissions_selector_keyboard(rank_id, current_perms, all_perms)
    )


@router.callback_query(F.data.startswith("toggle_perm:"))
@owner_only
async def toggle_permission(callback: CallbackQuery):
    _, rank_id, perm_code = callback.data.split(":")
    rank_id = int(rank_id)
    
    pool = await get_pool()
    current_perms = await get_rank_permissions(pool, rank_id)
    
    if perm_code in current_perms:
        current_perms.remove(perm_code)
        action = "إزالة"
    else:
        current_perms.append(perm_code)
        action = "إضافة"
    
    await set_rank_permissions(pool, rank_id, current_perms)
    
    all_perms = await get_permissions_list(pool)
    
    await callback.message.edit_reply_markup(
        reply_markup=permissions_selector_keyboard(rank_id, current_perms, all_perms)
    )
    await callback.answer(f"✅ تم {action}")


@router.callback_query(F.data.startswith("save_perms:"))
@owner_only
async def save_permissions(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    perms = await get_rank_permissions(pool, rank_id)
    
    await callback.message.edit_text(
        f"💾 <b>تم حفظ الصلاحيات!</b>\n\n"
        f"{rank['icon']} {rank['display_name']}\n"
        f"الصلاحيات: {len(perms)}",
        reply_markup=back_keyboard("ranks_panel")
    )


# ═══════════════════════════════════════
# حذف عضوية
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("delete_rank:"))
@owner_only
async def confirm_delete_rank(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    rank = await get_rank_by_id(pool, rank_id)
    if rank['is_protected']:
        await callback.answer("🔒 لا يمكن حذف العضوية المحمية!")
        return
    
    await callback.message.edit_text(
        f"⚠️ <b>تأكيد الحذف</b>\n\n"
        f"هل تريد حذف: {rank['icon']} {rank['display_name']}؟\n\n"
        f"❌ <b>تحذير:</b> الأعضاء بهذه العضوية سيتم نقلهم للعضو العادي!",
        reply_markup=confirm_delete_keyboard(rank_id)
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
@owner_only
async def execute_delete_rank(callback: CallbackQuery):
    rank_id = int(callback.data.split(":")[1])
    pool = await get_pool()
    
    await pool.execute("""
        UPDATE members SET rank_id = 4 WHERE rank_id = $1
    """, rank_id)
    
    deleted = await delete_rank(pool, rank_id)
    
    if deleted:
        await callback.message.edit_text(
            "✅ <b>تم حذف العضوية!</b>\n"
            "تم نقل الأعضاء للعضوية العادية.",
            reply_markup=back_keyboard("ranks_panel")
        )
    else:
        await callback.answer("❌ فشل الحذف!")
