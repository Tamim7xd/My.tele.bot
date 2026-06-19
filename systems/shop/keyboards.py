"""
لوحات المفاتيح (Inline Keyboards) لنظام المتجر (shop).

كل تفاعل حصري لمن فتح المتجر (owner_id محفوظ في كل callback_data).
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ مسح المخالفات/المحادثة", callback_data=f"shop:clear_intro:{owner_id}")],
            [InlineKeyboardButton(text="👑 شراء عضوية", callback_data=f"shop:memberships:{owner_id}:0")],
            [InlineKeyboardButton(text="🏷️ شراء لقب", callback_data=f"shop:titles:{owner_id}:0")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data=f"shop:close:{owner_id}")],
        ]
    )


def clear_chat_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تأكيد المسح", callback_data=f"shop:clear_confirm:{owner_id}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"shop:main:{owner_id}")],
        ]
    )


def memberships_list_keyboard(owner_id: int, memberships: list[dict], index: int) -> InlineKeyboardMarkup:
    """يعرض عضوية واحدة بالتنقل (التالي/رجوع) + رجوع للقائمة الرئيسية."""
    buttons = [
        [InlineKeyboardButton(text=memberships[index]["name"], callback_data="shop:noop")],
    ]

    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"shop:memberships:{owner_id}:{index - 1}"))

    if index < len(memberships) - 1:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"shop:memberships:{owner_id}:{index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="💰 شراء", callback_data=f"shop:buy_membership:{owner_id}:{memberships[index]['id']}")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data=f"shop:main:{owner_id}"),
        InlineKeyboardButton(text="❌ إغلاق", callback_data=f"shop:close:{owner_id}"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def titles_list_keyboard(owner_id: int, titles: list[dict], index: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=titles[index]["name"], callback_data="shop:noop")],
    ]

    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"shop:titles:{owner_id}:{index - 1}"))

    if index < len(titles) - 1:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"shop:titles:{owner_id}:{index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="💰 شراء", callback_data=f"shop:buy_title:{owner_id}:{titles[index]['id']}")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data=f"shop:main:{owner_id}"),
        InlineKeyboardButton(text="❌ إغلاق", callback_data=f"shop:close:{owner_id}"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"shop:main:{owner_id}")],
        ]
    )


# ===== أمر "لقب"/"مشترياتي" =====

def my_titles_keyboard(owned_titles: list[dict]) -> InlineKeyboardMarkup:
    buttons = []

    for title in owned_titles:
        buttons.append([
            InlineKeyboardButton(text=f"تفعيل {title['name']}", callback_data=f"shop:activate_title:{title['id']}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
