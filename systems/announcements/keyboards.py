"""
لوحات المفاتيح (Inline Keyboards) لنظام الإعلانات.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# مدد الحذف المتاحة (بالثواني)، 0 = بلا حذف
DELETE_AFTER_OPTIONS = [0, 5, 10, 30, 60]


def list_keyboard(announcements: list[dict]) -> InlineKeyboardMarkup:
    """قائمة الإعلانات + ➕ إضافة + 🔙 رجوع."""
    buttons = []

    for i, ann in enumerate(announcements):
        buttons.append([
            InlineKeyboardButton(text=f"📢 {ann['trigger']}", callback_data=f"owner:ann_view:{i}")
        ])

    buttons.append([InlineKeyboardButton(text="➕ إضافة إعلان", callback_data="owner:ann_add")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def announcement_details_keyboard(index: int) -> InlineKeyboardMarkup:
    """صفحة تفاصيل إعلان: تعديل النص / مدة الحذف / حذف الإعلان."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 تعديل النص", callback_data=f"owner:ann_edit_text:{index}")],
            [InlineKeyboardButton(text="⏱️ تعديل مدة الحذف", callback_data=f"owner:ann_edit_delete:{index}")],
            [InlineKeyboardButton(text="🗑️ حذف الإعلان", callback_data=f"owner:ann_delete:{index}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:announcements")],
        ]
    )


def delete_confirm_keyboard(index: int) -> InlineKeyboardMarkup:
    """تأكيد حذف إعلان."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ نعم، حذف", callback_data=f"owner:ann_delete_confirm:{index}")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data=f"owner:ann_view:{index}")],
        ]
    )


def delete_after_keyboard(index: int | None = None) -> InlineKeyboardMarkup:
    """
    لوحة اختيار مدة الحذف.
    index=None تعني أثناء الإضافة (إعلان جديد لم يُحفظ بعد).
    index=int تعني تعديل إعلان موجود.
    """
    target = "new" if index is None else str(index)

    buttons = []
    row = []

    for seconds in DELETE_AFTER_OPTIONS:
        label = "بلا حذف" if seconds == 0 else f"{seconds} ثانية"
        row.append(InlineKeyboardButton(text=label, callback_data=f"owner:ann_set_delete:{target}:{seconds}"))

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    if index is not None:
        buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:ann_view:{index}")])
    else:
        buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """زر إلغاء أثناء الإضافة/التعديل."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )
