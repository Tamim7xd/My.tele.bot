"""
لوحات المفاتيح لنظام العضويات الإدارية
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def ranks_list_keyboard(ranks: list) -> InlineKeyboardMarkup:
    """لوحة قائمة العضويات الإدارية"""
    builder = InlineKeyboardBuilder()
    
    for rank in ranks:
        protected = "🔒" if rank['is_protected'] else ""
        builder.button(
            text=f"{protected} {rank['icon']} {rank['display_name']}",
            callback_data=f"view_rank:{rank['id']}"
        )
    
    builder.button(text="➕ إضافة عضوية جديدة", callback_data="add_rank")
    builder.button(text="🔙 رجوع للوحة التحكم", callback_data="owner_panel")
    builder.adjust(1)
    
    return builder.as_markup()


def rank_details_keyboard(rank: dict) -> InlineKeyboardMarkup:
    """لوحة تفاصيل عضوية"""
    builder = InlineKeyboardBuilder()
    
    if not rank['is_protected']:
        builder.button(text="✏️ تعديل", callback_data=f"edit_rank:{rank['id']}")
        builder.button(text="⚡ الصلاحيات", callback_data=f"manage_perms:{rank['id']}")
        builder.button(text="🗑️ حذف", callback_data=f"delete_rank:{rank['id']}")
    
    builder.button(text="🔙 رجوع للقائمة", callback_data="ranks_panel")
    builder.adjust(1)
    
    return builder.as_markup()


def permissions_selector_keyboard(rank_id: int, current_perms: list, all_perms: list) -> InlineKeyboardMarkup:
    """محدد الصلاحيات حسب التصنيف"""
    builder = InlineKeyboardBuilder()
    
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
    
    for cat_name, perms in categories.items():
        display = cat_names.get(cat_name, cat_name)
        builder.button(text=f"─── {display} ───", callback_data="ignore")
        
        for perm in perms:
            is_active = perm['code'] in current_perms
            check = "✅" if is_active else "⬜"
            builder.button(
                text=f"{check} {perm['icon']} {perm['display_name']}",
                callback_data=f"toggle_perm:{rank_id}:{perm['code']}"
            )
    
    builder.button(text="💾 حفظ الصلاحيات", callback_data=f"save_perms:{rank_id}")
    builder.button(text="🔙 رجوع", callback_data=f"view_rank:{rank_id}")
    builder.adjust(1)
    
    return builder.as_markup()


def colors_keyboard() -> InlineKeyboardMarkup:
    """ألوان جاهزة للعضويات"""
    builder = InlineKeyboardBuilder()
    
    colors = [
        ("🔴 أحمر", "#FF4444"),
        ("🟢 أخضر", "#44FF44"),
        ("🔵 أزرق", "#4444FF"),
        ("🟡 أصفر", "#FFFF44"),
        ("🟣 بنفسجي", "#AA44FF"),
        ("🟠 برتقالي", "#FF8844"),
        ("⚪ فضي", "#C0C0C0"),
        ("🌟 ذهبي", "#FFD700"),
        ("⚫ أسود", "#333333"),
        ("🩷 وردي", "#FF69B4"),
    ]
    
    for name, code in colors:
        builder.button(text=name, callback_data=f"color:{code}")
    
    builder.button(text="❌ إلغاء", callback_data="ranks_panel")
    builder.adjust(2)
    
    return builder.as_markup()


def icons_keyboard() -> InlineKeyboardMarkup:
    """أيقونات جاهزة للعضويات"""
    builder = InlineKeyboardBuilder()
    
    icons = ["👤", "⭐", "🌟", "💎", "🏆", "👑", "🎖️", "🛡️", "⚔️", "🔥", 
             "⚡", "🎯", "🚀", "💪", "🦁", "🦅", "🐉", "❤️", "💚", "💙"]
    
    for icon in icons:
        builder.button(text=icon, callback_data=f"icon:{icon}")
    
    builder.button(text="❌ إلغاء", callback_data="ranks_panel")
    builder.adjust(5)
    
    return builder.as_markup()


def edit_rank_keyboard(rank_id: int) -> InlineKeyboardMarkup:
    """أزرار تعديل عضوية"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✏️ تغيير الاسم", callback_data=f"change_name:{rank_id}")
    builder.button(text="🎨 تغيير اللون", callback_data=f"change_color:{rank_id}")
    builder.button(text="🎯 تغيير الأيقونة", callback_data=f"change_icon:{rank_id}")
    builder.button(text="⚡ الصلاحيات", callback_data=f"manage_perms:{rank_id}")
    builder.button(text="🔙 رجوع", callback_data=f"view_rank:{rank_id}")
    builder.adjust(1)
    
    return builder.as_markup()


def confirm_delete_keyboard(rank_id: int) -> InlineKeyboardMarkup:
    """تأكيد حذف عضوية"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ نعم، احذف", callback_data=f"confirm_delete:{rank_id}")
    builder.button(text="❌ لا، تراجع", callback_data=f"view_rank:{rank_id}")
    builder.adjust(2)
    
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    """زر إلغاء"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ إلغاء", callback_data="ranks_panel")
    return builder.as_markup()


def back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """زر رجوع"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع", callback_data=callback_data)
    return builder.as_markup()
