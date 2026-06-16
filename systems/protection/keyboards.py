"""
لوحات المفاتيح (Inline Keyboards) لنظام الحماية.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from systems.protection.queries import FEATURE_KEYS, FEATURE_LABELS


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """لوحة تبديل كل ميزة + الكلمات المحظورة + رجوع."""
    buttons = []

    for key in FEATURE_KEYS:
        status_icon = "✅" if settings.get(key) else "❌"
        buttons.append([
            InlineKeyboardButton(text=f"{status_icon} {FEATURE_LABELS[key]}", callback_data=f"owner:prot_toggle:{key}")
        ])

    buttons.append([InlineKeyboardButton(text="📝 الكلمات المحظورة", callback_data="owner:prot_words:0")])
    buttons.append([InlineKeyboardButton(text="🗑️ لوحة المحذوفات", callback_data="owner:prot_deleted")])
    buttons.append([InlineKeyboardButton(text="🔄 إعادة تعيين الإعدادات", callback_data="owner:prot_reset")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def banned_words_keyboard(words: list[str], offset: int = 0, limit: int = 10) -> InlineKeyboardMarkup:
    """قائمة الكلمات المحظورة مع 🗑️ لكل كلمة + ➕ إضافة + رجوع."""
    buttons = []

    page_words = words[offset:offset + limit]

    for word in page_words:
        buttons.append([
            InlineKeyboardButton(text=f"📝 {word}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:prot_word_remove:{word}"),
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:prot_words:{offset - limit}"))

    if offset + limit < len(words):
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_words:{offset + limit}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="➕ إضافة كلمة", callback_data="owner:prot_word_add")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:protection")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:prot_words:0")],
        ]
    )


# ===== لوحة المحذوفات =====

def deleted_main_keyboard(violators_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👥 الأعضاء: {violators_count}", callback_data="owner:noop")],
            [InlineKeyboardButton(text="📋 عرض القائمة", callback_data="owner:prot_del_list:0")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:protection")],
        ]
    )


def deleted_list_keyboard(
    members: list[tuple[int, str | None, str, int]],
    offset: int,
    total: int,
    limit: int = 6,
) -> InlineKeyboardMarkup:
    """قائمة الأعضاء الذين لديهم محذوفات. members: (user_id, username, full_name, count)."""
    buttons = []

    for user_id, username, full_name, count in members:
        label = f"{full_name} | @{username} ({count})" if username else f"{full_name} ({count})"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:prot_del_member:{user_id}:0")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:prot_del_list:{offset - limit}"))

    if offset + limit < total:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_del_list:{offset + limit}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:prot_deleted")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_deleted_keyboard(user_id: int, page: int, total: int, limit: int = 5) -> InlineKeyboardMarkup:
    """
    صفحة محذوفات عضو: 5 لكل صفحة + التالي + ⚠️ تحذير + 🔇 كتم + 🔙 رجوع + ❌ إغلاق.
    """
    buttons = []

    if (page + 1) * limit < total:
        buttons.append([
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:prot_del_member:{user_id}:{page + 1}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⚠️ تحذير", callback_data=f"owner:prot_del_warn:{user_id}:{page}"),
        InlineKeyboardButton(text="🔇 كتم", callback_data=f"owner:prot_del_mute:{user_id}:{page}"),
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:prot_del_list:0"),
        InlineKeyboardButton(text="❌ إغلاق", callback_data="owner:prot_deleted"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== استثناءات فردية لعضو =====

def member_exceptions_keyboard(user_id: int, offset: int, exceptions: dict) -> InlineKeyboardMarkup:
    """قائمة الميزات مع حالة ✅/❌ استثناء العضو من كل واحدة."""
    buttons = []

    for key in FEATURE_KEYS:
        status_icon = "✅" if exceptions.get(key) else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {FEATURE_LABELS[key]}",
                callback_data=f"owner:prot_exc_toggle:{user_id}:{offset}:{key}",
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
