"""
لوحات المفاتيح (Inline Keyboards) لنظام الخصم والمكافأة.

القيم (REWARD_AMOUNTS_KEY) تُخزَّن في جدول settings (core/database.py)
وقابلة للتعديل من لوحة التحكم (systems/owner) دون التأثير على بنية الأزرار
أو الحاجة لإعادة نشر الكود.

DEFAULT_REWARD_AMOUNTS تُستخدم فقط كقيمة افتراضية أول مرة
(قبل أن يُحفظ أي تعديل في قاعدة البيانات).
"""

import asyncpg

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_setting


REWARD_AMOUNTS_KEY = "reward_amounts"
DEFAULT_REWARD_AMOUNTS = [1_000, 2_500, 5_000, 10_000]


async def get_reward_amounts(pool: asyncpg.Pool) -> list[int]:
    """يرجع قيم الخصم/المكافأة الحالية من قاعدة البيانات (أو الافتراضية)."""
    return await get_setting(pool, REWARD_AMOUNTS_KEY, DEFAULT_REWARD_AMOUNTS)


async def amount_keyboard(pool: asyncpg.Pool, action: str) -> InlineKeyboardMarkup:
    """
    لوحة اختيار المبلغ.
    action: "deduct" أو "reward"
    """
    amounts = await get_reward_amounts(pool)

    buttons = []

    # صفين، كل صف فيه زرين (شكل متناسق)
    for i in range(0, len(amounts), 2):
        row = []
        for amount in amounts[i:i + 2]:
            icon = "✂️" if action == "deduct" else "🎁"
            row.append(
                InlineKeyboardButton(
                    text=f"{icon} {amount:,}",
                    callback_data=f"rewards:amount:{action}:{amount}",
                )
            )
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="❌ إلغاء", callback_data=f"rewards:cancel:{action}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_reason_keyboard(action: str) -> InlineKeyboardMarkup:
    """لوحة "بدون سبب" التي تظهر عند طلب السبب."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ بدون سبب", callback_data=f"rewards:skip_reason:{action}")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data=f"rewards:cancel:{action}")],
        ]
    )


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """لوحة التأكيد النهائي."""
    buttons = [
        [InlineKeyboardButton(text="✅ تأكيد", callback_data=f"rewards:confirm:{action}")],
    ]

    # خيار "تأكيد + مخالفة" فقط للخصم
    if action == "deduct":
        buttons.append([
            InlineKeyboardButton(text="⚠️ تأكيد + مخالفة", callback_data=f"rewards:confirm_violation:{action}")
        ])

    buttons.append([
        InlineKeyboardButton(text="❌ إلغاء", callback_data=f"rewards:cancel:{action}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
