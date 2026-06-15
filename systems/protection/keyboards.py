"""
لوحات مفاتيح نظام الحماية
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from systems.protection.queries import FEATURE_KEYS, FEATURE_LABELS


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """لوحة إعدادات الحماية الرئيسية"""
    buttons = []
    
    for key in FEATURE_KEYS:
        status = "✅" if settings.get(key) else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {FEATURE_LABELS[key]}",
                callback_data=f"owner:prot_toggle:{key}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="📝 الكلمات المحظورة", callback_data="owner:prot_words:0")])
    buttons.append([InlineKeyboardButton(text="🗑️ لوحة المحذوفات", callback_data="owner:prot_deleted")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def banned_words_keyboard(words: list, offset: int = 0, limit: int = 10) -> InlineKeyboardMarkup:
    """لوحة الكلمات المحظورة"""
    buttons = []
    
    page_words = words[offset:offset + limit]
    
    for word in page_words:
        display_word = word[:27] + "..." if len(word) > 30 else word
        buttons.append([
            InlineKeyboardButton(text=f"📝 {display_word}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:prot_word_remove:{word}"),
        ])
    
    nav_row = []
    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"owner:prot_words:{offset - limit}"))
    if offset + limit < len(words):
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_words:{offset + limit}"))
    if nav_row:
        buttons.append(nav_row)
    
    if words:
        page_num = offset // limit + 1
        total_pages = ((len(words) - 1) // limit) + 1
        buttons.append([InlineKeyboardButton(text=f"📄 صفحة {page_num} من {total_pages}", callback_data="owner:noop")])
    
    buttons.append([InlineKeyboardButton(text="➕ إضافة كلمة", callback_data="owner:prot_word_add")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:protection")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """لوحة إلغاء"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:prot_words:0")],
        ]
    )


def deleted_main_keyboard(violators_count: int) -> InlineKeyboardMarkup:
    """لوحة المحذوفات الرئيسية"""
    buttons = []
    if violators_count > 0:
        buttons.append([InlineKeyboardButton(text="👥 المخالفون", callback_data="owner:noop")])
        buttons.append([InlineKeyboardButton(text="📋 عرض القائمة", callback_data="owner:prot_del_list:0")])
    else:
        buttons.append([InlineKeyboardButton(text="✨ لا يوجد مخالفون", callback_data="owner:noop")])
    
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:protection")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def deleted_list_keyboard(members: list, offset: int, total: int, limit: int = 6) -> InlineKeyboardMarkup:
    """قائمة المخالفين"""
    buttons = []
    
    for user_id, username, full_name, count in members:
        if username:
            label = f"{full_name[:20]} | @{username} ({count})"
        else:
            label = f"{full_name[:25]} ({count})"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:prot_del_member:{user_id}:0")
        ])
    
    nav_row = []
    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"owner:prot_del_list:{offset - limit}"))
    if offset + limit < total:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_del_list:{offset + limit}"))
    if nav_row:
        buttons.append(nav_row)
    
    if total > 0:
        current_page = offset // limit + 1
        total_pages = (total - 1) // limit + 1
        buttons.append([InlineKeyboardButton(text=f"📄 صفحة {current_page} من {total_pages}", callback_data="owner:noop")])
    
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:prot_deleted")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_deleted_keyboard(user_id: int, page: int, total: int, limit: int = 5) -> InlineKeyboardMarkup:
    """صفحة محذوفات عضو"""
    buttons = []
    
    if (page + 1) * limit < total:
        buttons.append([
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_del_member:{user_id}:{page + 1}")
        ])
    
    if total > 0:
        current_page = page + 1
        total_pages = (total - 1) // limit + 1
        buttons.append([InlineKeyboardButton(text=f"📄 صفحة {current_page} من {total_pages}", callback_data="owner:noop")])
    
    buttons.append([
        InlineKeyboardButton(text="⚠️ تحذير", callback_data=f"owner:prot_del_warn:{user_id}:{page}"),
        InlineKeyboardButton(text="🔇 كتم 10 دقائق", callback_data=f"owner:prot_del_mute:{user_id}:{page}"),
    ])
    
    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع للقائمة", callback_data="owner:prot_del_list:0"),
        InlineKeyboardButton(text="❌ إغلاق", callback_data="owner:prot_deleted"),
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_exceptions_keyboard(user_id: int, offset: int, exceptions: dict) -> InlineKeyboardMarkup:
    """لوحة استثناءات عضو"""
    buttons = []
    
    for key in FEATURE_KEYS:
        status = "✅" if exceptions.get(key) else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {FEATURE_LABELS[key]}",
                callback_data=f"owner:prot_exc_toggle:{user_id}:{offset}:{key}",
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="ℹ️ ما هي الاستثناءات؟", callback_data="owner:prot_exc_help")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def exceptions_help_keyboard(user_id: int, offset: int) -> InlineKeyboardMarkup:
    """لوحة مساعدة الاستثناءات"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع للاستثناءات", callback_data=f"owner:prot_exc:{user_id}:{offset}")],
            [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="owner:main")],
        ]
    )