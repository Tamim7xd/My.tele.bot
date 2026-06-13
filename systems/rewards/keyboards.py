"""
لوحات المفاتيح (Inline Keyboards) لنظام الخصم والمكافأة.

القيم الثابتة هنا (REWARD_AMOUNTS) مؤقتة وستكون قابلة
للتعديل من لوحة التحكم لاحقاً دون التأثير على بنية الأزرار.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ===== القيم الافتراضية (مؤقتة - قابلة للتعديل من لوحة التحكم لاحقاً) =====
REWARD_AMOUNTS = [1_000, 2_500, 5_000, 10_000]


def amount_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    لوحة اختيار المبلغ.
    action: "deduct" أو "reward"
    """
    buttons = []

    # صفين، كل صف فيه زرين (شكل متناسق)
    for i in range(0, len(REWARD_AMOUNTS), 2):
        row = []
        for amount in REWARD_AMOUNTS[i:i + 2]:
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
