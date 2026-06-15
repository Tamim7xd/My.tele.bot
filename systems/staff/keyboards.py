"""
لوحات المفاتيح (Inline Keyboards) لـ "مشرف"/"ادمن".
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard(violators_count: int) -> InlineKeyboardMarkup:
    """
    القائمة الرئيسية: زر غير قابل للضغط بعدد المخالفين + زر القائمة.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔴 المخالفون: {violators_count}", callback_data="staff:noop")],
            [InlineKeyboardButton(text="📋 قائمة المخالفين", callback_data="staff:list:0")],
        ]
    )


def violators_list_keyboard(
    is_admin: bool,
    members: list[tuple[int, str | None, str]],
    offset: int,
    total: int,
    limit: int = 5,
) -> InlineKeyboardMarkup:
    """قائمة المخالفين، 5 لكل صفحة، مع التالي/رجوع/إغلاق."""
    prefix = "admin" if is_admin else "mod"

    buttons = []

    for user_id, username, full_name in members:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"staff:{prefix}:member:{user_id}:{offset}")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️ رجوع", callback_data=f"staff:list:{offset - limit}")
        )

    if offset + limit < total:
        nav_row.append(
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"staff:list:{offset + limit}")
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="❌ إغلاق", callback_data="staff:close")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_page_keyboard(is_admin: bool, user_id: int, offset: int, is_muted: bool, is_banned: bool) -> InlineKeyboardMarkup:
    """
    صفحة عضو من قائمة المخالفين:
    - فتح الكتم (إن كان مكتوماً)
    - تمديد الكتم
    - تخفيض التحذيرات
    - إلغاء الحظر (أدمن فقط، إن كان محظوراً)
    """
    prefix = "admin" if is_admin else "mod"

    buttons = []

    if is_muted:
        buttons.append([
            InlineKeyboardButton(text="🔊 فتح الكتم", callback_data=f"staff:{prefix}:unmute:{user_id}:{offset}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⏳ تمديد الكتم", callback_data=f"staff:{prefix}:extend:{user_id}:{offset}")
    ])

    if is_admin and is_banned:
        buttons.append([
            InlineKeyboardButton(text="✅ إلغاء الحظر", callback_data=f"staff:{prefix}:unban:{user_id}:{offset}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⬇️ تخفيض التحذيرات", callback_data=f"staff:{prefix}:reduce_warn:{user_id}:{offset}")
    ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"staff:list:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== فئات ومدد تمديد الكتم (نفس فئات moderation) =====

def extend_category_keyboard(is_admin: bool, user_id: int, offset: int) -> InlineKeyboardMarkup:
    from systems.moderation.keyboards import MUTE_DURATIONS, CATEGORY_LABELS

    prefix = "admin" if is_admin else "mod"

    buttons = []
    row = []

    for category in MUTE_DURATIONS:
        row.append(
            InlineKeyboardButton(
                text=CATEGORY_LABELS[category],
                callback_data=f"staff:{prefix}:ext_cat:{user_id}:{offset}:{category}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"staff:{prefix}:member:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def extend_duration_keyboard(is_admin: bool, category: str, user_id: int, offset: int) -> InlineKeyboardMarkup:
    from systems.moderation.keyboards import MUTE_DURATIONS
    from systems.moderation.notifications.messages import duration_label

    prefix = "admin" if is_admin else "mod"
    seconds_list = MUTE_DURATIONS[category]

    buttons = []
    row = []

    for seconds in seconds_list:
        row.append(
            InlineKeyboardButton(
                text=duration_label(seconds),
                callback_data=f"staff:{prefix}:ext_dur:{user_id}:{offset}:{seconds}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data=f"staff:{prefix}:extend:{user_id}:{offset}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
