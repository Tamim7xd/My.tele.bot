"""
لوحات المفاتيح (Inline Keyboards) لنظام الأرشيف.

نمط التنقل:
👥 الأعضاء (members_panel) أو 📁 الأرشيف (قائمة مستقلة)
    ↓ اختيار عضو
📁 أرشيف العضو (6 فئات + 📋 العدد الكامل)
    ↓ اختيار فئة
تفاصيل الفئة (آخر 10) + 📋 نسخ + 🔙 رجوع

source: "list" (من قائمة الأرشيف المستقلة) أو "members" (من صفحة العضو
في 👥 الأعضاء) - يُحفظ في كل callback_data ليعرف زر الرجوع لأين يذهب.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from systems.archive.notifications.messages import CATEGORY_LABELS


def _suffix(source: str) -> str:
    return f":{source}" if source else ""


def archive_list_keyboard(
    members: list[tuple[int, str | None, str]],
    offset: int,
    total: int,
    limit: int = 6,
) -> InlineKeyboardMarkup:
    """قائمة أعضاء مستقلة لزر '📁 الأرشيف' في القائمة الرئيسية."""
    buttons = []

    for user_id, username, full_name in members:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:archive_member:{user_id}:{offset}:list")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:archive_list:{offset - limit}")
        )

    if offset + limit < total:
        nav_row.append(
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:archive_list:{offset + limit}")
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔍 بحث", callback_data="owner:archive_search")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def archive_search_results_keyboard(results: list[tuple[int, str | None, str]]) -> InlineKeyboardMarkup:
    """نتائج البحث في قائمة الأرشيف المستقلة."""
    buttons = []

    for user_id, username, full_name in results:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:archive_member:{user_id}:0:list")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:archive_list:0")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def archive_main_keyboard(user_id: int, offset: int, source: str) -> InlineKeyboardMarkup:
    """
    صفحة أرشيف العضو: 6 فئات + 📋 العدد الكامل + 🔙 رجوع.

    source: "list" أو "members" - يحدد إلى أين يعود زر الرجوع.
    """
    buttons = []

    for action_type, label in CATEGORY_LABELS.items():
        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"owner:arch_cat:{action_type}:{user_id}:{offset}:{source}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="📋 العدد الكامل", callback_data=f"owner:arch_summary:{user_id}:{offset}:{source}")
    ])

    if source == "members":
        back_callback = f"owner:member:{user_id}:{offset}"
    else:
        back_callback = f"owner:archive_list:{offset}"

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_entries_keyboard(action_type: str, user_id: int, offset: int, source: str) -> InlineKeyboardMarkup:
    """صفحة تفاصيل فئة: 📋 نسخ + 🔙 رجوع لصفحة الأرشيف."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 نسخ", callback_data=f"owner:arch_copy:{action_type}:{user_id}:{offset}:{source}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:archive_member:{user_id}:{offset}:{source}")],
        ]
    )


def full_summary_keyboard(user_id: int, offset: int, source: str) -> InlineKeyboardMarkup:
    """صفحة العدد الكامل: 📋 نسخ + 🔙 رجوع لصفحة الأرشيف."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 نسخ", callback_data=f"owner:arch_summary_copy:{user_id}:{offset}:{source}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:archive_member:{user_id}:{offset}:{source}")],
        ]
    )
