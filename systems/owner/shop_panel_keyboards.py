"""
لوحات المفاتيح (Inline Keyboards) لـ "🛒 المتجر" في لوحة التحكم.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def shop_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 العضويات", callback_data="owner:shop_memberships:0")],
            [InlineKeyboardButton(text="🏷️ الألقاب", callback_data="owner:shop_titles:0")],
            [InlineKeyboardButton(text="🗑️ إعدادات مسح المحادثة", callback_data="owner:shop_clear_settings")],
            [InlineKeyboardButton(text="📁 أرشيف المتجر", callback_data="owner:shop_archive")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:shop")],
        ]
    )


# ===== العضويات =====

def memberships_list_keyboard(memberships: list[dict], index: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=memberships[index]["name"], callback_data="owner:noop")],
    ]

    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:shop_memberships:{index - 1}"))

    if index < len(memberships) - 1:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:shop_memberships:{index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    membership_id = memberships[index]["id"]

    buttons.append([InlineKeyboardButton(text="✏️ تعديل الاسم", callback_data=f"owner:mship_edit_name:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="💰 تعديل السعر", callback_data=f"owner:mship_edit_price:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="⏳ تعديل المدة", callback_data=f"owner:mship_edit_duration:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="🎁 تعديل المكافأة اليومية", callback_data=f"owner:mship_edit_reward:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="🗑️ cooldown المسح", callback_data=f"owner:mship_edit_cooldown:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="⚙️ تبديل المزايا", callback_data=f"owner:mship_features:{membership_id}")])
    buttons.append([InlineKeyboardButton(text="📋 من اشتراها", callback_data=f"owner:mship_owners:{membership_id}:0")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def membership_features_keyboard(membership: dict) -> InlineKeyboardMarkup:
    membership_id = membership["id"]

    def icon(key: str) -> str:
        return "✅" if membership.get(key) else "❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{icon('can_clear_chat')} مسح المحادثة",
                callback_data=f"owner:mship_toggle:{membership_id}:can_clear_chat",
            )],
            [InlineKeyboardButton(
                text=f"{icon('can_send_media')} إرسال الوسائط",
                callback_data=f"owner:mship_toggle:{membership_id}:can_send_media",
            )],
            [InlineKeyboardButton(
                text=f"{icon('no_replies')} منع الرد عليه",
                callback_data=f"owner:mship_toggle:{membership_id}:no_replies",
            )],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop_memberships:0")],
        ]
    )


def duration_unit_keyboard(membership_id: str) -> InlineKeyboardMarkup:
    """اختيار وحدة الزمن (دقائق/ساعات/أيام/أشهر) قبل طلب الرقم."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱️ دقائق", callback_data=f"owner:mship_dur_unit:{membership_id}:minutes"),
                InlineKeyboardButton(text="🕐 ساعات", callback_data=f"owner:mship_dur_unit:{membership_id}:hours"),
            ],
            [
                InlineKeyboardButton(text="📅 أيام", callback_data=f"owner:mship_dur_unit:{membership_id}:days"),
                InlineKeyboardButton(text="🗓️ أشهر", callback_data=f"owner:mship_dur_unit:{membership_id}:months"),
            ],
            [InlineKeyboardButton(text="♾️ دائمة (بلا انتهاء)", callback_data=f"owner:mship_dur_permanent:{membership_id}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop_memberships:0")],
        ]
    )


def owners_list_keyboard(membership_id: str, offset: int, total: int, limit: int = 5) -> InlineKeyboardMarkup:
    buttons = []

    nav_row = []

    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:mship_owners:{membership_id}:{offset - limit}"))

    if offset + limit < total:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:mship_owners:{membership_id}:{offset + limit}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop_memberships:0")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== الألقاب =====

def titles_list_keyboard(titles: list[dict], index: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=titles[index]["name"], callback_data="owner:noop")],
    ]

    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:shop_titles:{index - 1}"))

    if index < len(titles) - 1:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:shop_titles:{index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    title_id = titles[index]["id"]

    buttons.append([InlineKeyboardButton(text="✏️ تعديل الاسم", callback_data=f"owner:title_edit_name:{title_id}")])
    buttons.append([InlineKeyboardButton(text="💰 تعديل السعر", callback_data=f"owner:title_edit_price:{title_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== إعدادات مسح المحادثة =====

def clear_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 تعديل السعر", callback_data="owner:shop_clear_price")],
            [InlineKeyboardButton(text="🔢 تعديل نطاق الحذف", callback_data="owner:shop_clear_range")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop")],
        ]
    )


# ===== أرشيف المتجر =====

def archive_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ سجل مسح المحادثات", callback_data="owner:shop_clear_archive:0")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop")],
        ]
    )


def clear_archive_list_keyboard(members: list[tuple], offset: int, total: int, limit: int = 6) -> InlineKeyboardMarkup:
    buttons = []

    for user_id, username, full_name, count in members:
        label = f"{full_name} | @{username} ({count})" if username else f"{full_name} ({count})"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:shop_clear_member:{user_id}:0")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:shop_clear_archive:{offset - limit}"))

    if offset + limit < total:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:shop_clear_archive:{offset + limit}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop_archive")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def clear_member_history_keyboard(user_id: int, page: int, total: int, limit: int = 5) -> InlineKeyboardMarkup:
    buttons = []

    if (page + 1) * limit < total:
        buttons.append([
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:shop_clear_member:{user_id}:{page + 1}")
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:shop_clear_archive:0"),
        InlineKeyboardButton(text="❌ إغلاق", callback_data="owner:shop_archive"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== إدارة عضوية عضو من صفحته (👥 الأعضاء) =====

def member_membership_keyboard(user_id: int, offset: int, has_membership: bool) -> InlineKeyboardMarkup:
    buttons = []

    if has_membership:
        buttons.append([
            InlineKeyboardButton(text="❌ سحب العضوية", callback_data=f"owner:mship_revoke:{user_id}:{offset}")
        ])
        buttons.append([
            InlineKeyboardButton(text="⏳ تمديد/تقليص (أيام)", callback_data=f"owner:mship_extend:{user_id}:{offset}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="➕ منح عضوية", callback_data=f"owner:mship_grant:{user_id}:{offset}:0")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def grant_membership_keyboard(user_id: int, offset: int, memberships: list[dict], index: int) -> InlineKeyboardMarkup:
    """اختيار عضوية لمنحها مباشرة لعضو (بدون دفع) من اللوحة."""
    buttons = [
        [InlineKeyboardButton(text=memberships[index]["name"], callback_data="owner:noop")],
    ]

    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:mship_grant:{user_id}:{offset}:{index - 1}"))

    if index < len(memberships) - 1:
        nav_row.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:mship_grant:{user_id}:{offset}:{index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    membership_id = memberships[index]["id"]

    buttons.append([
        InlineKeyboardButton(text="✅ منح هذه العضوية", callback_data=f"owner:mship_grant_confirm:{user_id}:{offset}:{membership_id}")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member_mship:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
