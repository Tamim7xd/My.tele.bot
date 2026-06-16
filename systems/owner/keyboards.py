"""
لوحات مفاتيح "لوحة التحكم".
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="owner:members:0")],
            [InlineKeyboardButton(text="📁 الأرشيف", callback_data="owner:archive_list:0")],
            [InlineKeyboardButton(text="👮 الإداريين", callback_data="owner:moderators")],
            [InlineKeyboardButton(text="👑 إدارة العضويات", callback_data="owner:ranks")],  # ⭐ جديد
            [InlineKeyboardButton(text="💰 الرصيد", callback_data="owner:wallet")],
            [InlineKeyboardButton(text="💸 الخصم والمكافأة", callback_data="owner:rewards")],
            [InlineKeyboardButton(text="📊 المستويات", callback_data="owner:levels")],
            [InlineKeyboardButton(text="📢 الإعلانات", callback_data="owner:announcements")],
            [InlineKeyboardButton(text="🛡️ الحماية", callback_data="owner:protection")],
            [InlineKeyboardButton(text="🧹 التنظيف", callback_data="owner:cleanup")],
        ]
    )
