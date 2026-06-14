"""
لوحات المفاتيح (Inline Keyboards) لنظام الحظر/الكتم/التحذير.

التدفق:
رد + "كتم"/"حظر" -> فئة المدة (ثواني/دقائق/ساعات/أيام) -> مدة محددة -> تأكيد (+ مخالفة للكتم/الحظر)
رد + "تحذير" -> تأكيد مباشرة
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ===== المدد المتاحة لكل فئة (بالثواني) =====

MUTE_DURATIONS = {
    "seconds": [30, 60],
    "minutes": [5 * 60, 10 * 60, 15 * 60, 30 * 60],
    "hours": [3600, 3 * 3600, 6 * 3600, 12 * 3600],
    "days": [86400, 3 * 86400, 7 * 86400],
}

BAN_DURATIONS = {
    "minutes": [5 * 60, 10 * 60, 15 * 60, 30 * 60],
    "hours": [3600, 3 * 3600, 6 * 3600, 12 * 3600],
    "days": [86400, 3 * 86400, 7 * 86400],
}

CATEGORY_LABELS = {
    "seconds": "⏱️ ثواني",
    "minutes": "🕐 دقائق",
    "hours": "🕑 ساعات",
    "days": "📅 أيام",
}


def category_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    لوحة اختيار فئة المدة (ثواني/دقائق/ساعات/أيام).
    action: "mute" أو "ban"
    """
    durations = MUTE_DURATIONS if action == "mute" else BAN_DURATIONS

    buttons = []
    row = []

    for category in durations:
        row.append(
            InlineKeyboardButton(text=CATEGORY_LABELS[category], callback_data=f"moderation:cat:{action}:{category}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data=f"moderation:cancel:{action}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duration_keyboard(action: str, category: str) -> InlineKeyboardMarkup:
    """لوحة اختيار مدة محددة من فئة معينة."""
    durations = MUTE_DURATIONS if action == "mute" else BAN_DURATIONS
    seconds_list = durations[category]

    from systems.moderation.notifications.messages import duration_label

    buttons = []
    row = []

    for seconds in seconds_list:
        row.append(
            InlineKeyboardButton(text=duration_label(seconds), callback_data=f"moderation:dur:{action}:{seconds}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"moderation:cat_back:{action}")])
    buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data=f"moderation:cancel:{action}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard(action: str, with_violation: bool = True) -> InlineKeyboardMarkup:
    """لوحة التأكيد النهائي (للكتم والحظر تظهر "+ مخالفة")."""
    buttons = [
        [InlineKeyboardButton(text="✅ تأكيد", callback_data=f"moderation:confirm:{action}")],
    ]

    if with_violation:
        buttons.append([
            InlineKeyboardButton(text="⚠️ تأكيد + مخالفة", callback_data=f"moderation:confirm_violation:{action}")
        ])

    buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data=f"moderation:cancel:{action}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def warn_confirm_keyboard() -> InlineKeyboardMarkup:
    """لوحة تأكيد التحذير (بدون خيار مخالفة - التحذير نفسه هو الإجراء)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تأكيد", callback_data="moderation:confirm:warn")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="moderation:cancel:warn")],
        ]
    )
