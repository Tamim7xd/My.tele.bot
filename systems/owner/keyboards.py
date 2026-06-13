"""
لوحات المفاتيح (Inline Keyboards) لـ "لوحة التحكم".

كل نظام جديد يُبنى مستقبلاً يُضاف له زر هنا فقط،
بدون التأثير على الأزرار الأخرى.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """القائمة الرئيسية لـ لوحة التحكم."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👮 الإداريين", callback_data="owner:moderators")],
            [InlineKeyboardButton(text="💰 الرصيد", callback_data="owner:wallet")],
            [InlineKeyboardButton(text="💸 الخصم والمكافأة", callback_data="owner:rewards")],
            [InlineKeyboardButton(text="🧹 التنظيف", callback_data="owner:cleanup")],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    """زر رجوع للقائمة الرئيسية."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )
