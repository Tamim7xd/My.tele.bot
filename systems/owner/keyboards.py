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
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="owner:members:0")],
            [InlineKeyboardButton(text="📁 الأرشيف", callback_data="owner:archive_list:0")],
            [InlineKeyboardButton(text="👮 الإداريين", callback_data="owner:moderators")],
            [InlineKeyboardButton(text="💰 الرصيد", callback_data="owner:wallet")],
            [InlineKeyboardButton(text="💸 الخصم والمكافأة", callback_data="owner:rewards")],
            [InlineKeyboardButton(text="📊 المستويات", callback_data="owner:levels")],
            [InlineKeyboardButton(text="📢 الإعلانات", callback_data="owner:announcements")],
            [InlineKeyboardButton(text="🛡️ الحماية", callback_data="owner:protection")],
            [InlineKeyboardButton(text="🎮 الألعاب", callback_data="owner:games")],
            [InlineKeyboardButton(text="🛒 المتجر", callback_data="owner:shop")],
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


def rewards_keyboard(amounts: list[int]) -> InlineKeyboardMarkup:
    """
    لوحة نظام الخصم والمكافأة - تعرض كل قيمة مع زر 🗑️ حذف بجانبها،
    وزر ➕ إضافة قيمة جديدة في الأسفل.
    """
    buttons = []

    for amount in amounts:
        buttons.append([
            InlineKeyboardButton(text=f"💰 {amount:,}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:rewards:remove:{amount}"),
        ])

    buttons.append([InlineKeyboardButton(text="➕ إضافة قيمة", callback_data="owner:rewards:add")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cleanup_keyboard() -> InlineKeyboardMarkup:
    """لوحة نظام التنظيف - مع زر تعديل العدد."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ تعديل العدد", callback_data="owner:cleanup:edit")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def cancel_edit_keyboard() -> InlineKeyboardMarkup:
    """زر إلغاء أثناء انتظار إدخال قيمة جديدة."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:cancel_edit")],
        ]
    )


# ===== لوحات نظام الإداريين =====

def moderators_main_keyboard(admin_count: int, moderator_count: int) -> InlineKeyboardMarkup:
    """قائمة "الأدمن (عدد) / المشرفين (عدد)"."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🛡️ الأدمن ({admin_count})", callback_data="owner:mod_list:admin:0")],
            [InlineKeyboardButton(text=f"🔧 المشرفين ({moderator_count})", callback_data="owner:mod_list:moderator:0")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def staff_list_keyboard(
    rank: str,
    members: list[tuple[int, str | None, str]],
    offset: int,
    total: int,
    limit: int = 6,
) -> InlineKeyboardMarkup:
    """
    قائمة أعضاء برتبة معينة (admin أو moderator)، 6 لكل صفحة،
    مع أزرار ◀️ رجوع / التالي ▶️ عند الحاجة.

    members: قائمة من (user_id, username, full_name)
    """
    buttons = []

    for user_id, username, full_name in members:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:mod_member:{rank}:{user_id}:{offset}")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:mod_list:{rank}:{offset - limit}")
        )

    if offset + limit < total:
        nav_row.append(
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:mod_list:{rank}:{offset + limit}")
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:moderators")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def staff_member_keyboard(rank: str, user_id: int, offset: int) -> InlineKeyboardMarkup:
    """صفحة عضو محدد: ترقية / تخفيض / الصلاحيات / رجوع."""
    buttons = []

    if rank == "moderator":
        buttons.append([
            InlineKeyboardButton(text="⬆️ ترقية لأدمن", callback_data=f"owner:mod_promote:{user_id}:{rank}:{offset}")
        ])
        buttons.append([
            InlineKeyboardButton(text="⬇️ تخفيض لعضو", callback_data=f"owner:mod_demote:{user_id}:{rank}:{offset}")
        ])
    elif rank == "admin":
        buttons.append([
            InlineKeyboardButton(text="⬇️ تخفيض لمشرف", callback_data=f"owner:mod_demote:{user_id}:{rank}:{offset}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⚙️ الصلاحيات", callback_data=f"owner:mod_perms:{user_id}:{rank}:{offset}")
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:mod_list:{rank}:{offset}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# الصلاحيات القابلة للتفعيل/الإيقاف من اللوحة
TOGGLEABLE_PERMISSIONS = {
    "mute": "🔇 كتم",
    "deduct": "✂️ خصم",
    "ban": "🚫 حظر",
    "reward": "🎁 مكافأة",
    "warn": "⚠️ تحذير",
}


def permissions_keyboard(
    user_id: int,
    rank: str,
    offset: int,
    active_permissions: set[str],
) -> InlineKeyboardMarkup:
    """قائمة الصلاحيات مع حالة ✅/❌ لكل صلاحية، قابلة للضغط للتبديل."""
    buttons = []

    for perm_key, perm_label in TOGGLEABLE_PERMISSIONS.items():
        status_icon = "✅" if perm_key in active_permissions else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {perm_label}",
                callback_data=f"owner:mod_toggle_perm:{user_id}:{rank}:{offset}:{perm_key}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:mod_member:{rank}:{user_id}:{offset}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== لوحات نظام الأعضاء (members) =====

def members_list_keyboard(
    members: list[tuple[int, str | None, str]],
    offset: int,
    total: int,
    limit: int = 6,
) -> InlineKeyboardMarkup:
    """
    قائمة جميع الأعضاء، 6 لكل صفحة، مع أزرار ◀️ رجوع / التالي ▶️.

    members: قائمة من (user_id, username, full_name)
    """
    buttons = []

    for user_id, username, full_name in members:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:member:{user_id}:{offset}")
        ])

    nav_row = []

    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️ رجوع", callback_data=f"owner:members:{offset - limit}")
        )

    if offset + limit < total:
        nav_row.append(
            InlineKeyboardButton(text="التالي ▶️", callback_data=f"owner:members:{offset + limit}")
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔍 بحث", callback_data="owner:member_search")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_page_keyboard(user_id: int, offset: int, rank: str, is_muted: bool = False, is_banned: bool = False) -> InlineKeyboardMarkup:
    """
    صفحة عضو كاملة من قائمة الأعضاء العامة:
    تعديل الرصيد + تعديل المستوى + تعديل الرتبة + كتم/حظر + رجوع لقائمة الأعضاء.

    offset: نستخدمه لمعرفة من أين أتى العضو (للرجوع لنفس الصفحة).
    rank: الرتبة الحالية، لتحديد أزرار الترقية/التخفيض المناسبة.
    is_muted/is_banned: لعرض زر "رفع الكتم/الحظر" بدل "كتم/حظر".
    """
    buttons = [
        [InlineKeyboardButton(text="💰 تعديل الرصيد", callback_data=f"owner:member_balance:{user_id}:{offset}")],
        [InlineKeyboardButton(text="📊 تعديل المستوى", callback_data=f"owner:member_level:{user_id}:{offset}")],
    ]

    if rank in ("member", "moderator"):
        buttons.append([
            InlineKeyboardButton(text="⬆️ ترقية", callback_data=f"owner:member_promote:{user_id}:{offset}")
        ])

    if rank in ("moderator", "admin"):
        buttons.append([
            InlineKeyboardButton(text="⬇️ تخفيض", callback_data=f"owner:member_demote:{user_id}:{offset}")
        ])

    if rank in ("moderator", "admin"):
        buttons.append([
            InlineKeyboardButton(text="⚙️ الصلاحيات", callback_data=f"owner:mod_perms:{user_id}:{rank}:{offset}")
        ])

    # ===== أزرار moderation =====
    if is_muted:
        buttons.append([
            InlineKeyboardButton(text="🔊 رفع الكتم", callback_data=f"owner:member_unmute:{user_id}:{offset}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔇 كتم", callback_data=f"owner:member_mute:{user_id}:{offset}")
        ])

    if is_banned:
        buttons.append([
            InlineKeyboardButton(text="✅ رفع الحظر", callback_data=f"owner:member_unban:{user_id}:{offset}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🚫 حظر", callback_data=f"owner:member_ban:{user_id}:{offset}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⚠️ تحذير", callback_data=f"owner:member_warn:{user_id}:{offset}")
    ])

    buttons.append([
        InlineKeyboardButton(text="📁 الأرشيف", callback_data=f"owner:archive_member:{user_id}:{offset}:members")
    ])

    buttons.append([
        InlineKeyboardButton(text="🛡️ استثناءات الحماية", callback_data=f"owner:prot_exc:{user_id}:{offset}")
    ])

    buttons.append([
        InlineKeyboardButton(text="👑 إدارة العضوية", callback_data=f"owner:member_mship:{user_id}:{offset}")
    ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:members:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_mute_ban_duration_keyboard(action: str, user_id: int, offset: int) -> InlineKeyboardMarkup:
    """
    لوحة اختيار فئة المدة للكتم/الحظر من صفحة العضو في اللوحة
    (نفس فئات systems/moderation/keyboards لكن بسياق اللوحة).
    """
    from systems.moderation.keyboards import MUTE_DURATIONS, BAN_DURATIONS, CATEGORY_LABELS

    durations = MUTE_DURATIONS if action == "mute" else BAN_DURATIONS

    buttons = []
    row = []

    for category in durations:
        row.append(
            InlineKeyboardButton(
                text=CATEGORY_LABELS[category],
                callback_data=f"owner:mb_cat:{action}:{user_id}:{offset}:{category}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_mute_ban_duration_list_keyboard(action: str, category: str, user_id: int, offset: int) -> InlineKeyboardMarkup:
    """لوحة اختيار مدة محددة (للكتم/الحظر من صفحة العضو في اللوحة)."""
    from systems.moderation.keyboards import MUTE_DURATIONS, BAN_DURATIONS
    from systems.moderation.notifications.messages import duration_label

    durations = MUTE_DURATIONS if action == "mute" else BAN_DURATIONS
    seconds_list = durations[category]

    buttons = []
    row = []

    for seconds in seconds_list:
        row.append(
            InlineKeyboardButton(
                text=duration_label(seconds),
                callback_data=f"owner:mb_dur:{action}:{user_id}:{offset}:{seconds}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:mb_action:{action}:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def member_warn_confirm_keyboard(user_id: int, offset: int) -> InlineKeyboardMarkup:
    """لوحة تأكيد التحذير من صفحة العضو في اللوحة."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تأكيد", callback_data=f"owner:mb_warn_confirm:{user_id}:{offset}")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data=f"owner:member:{user_id}:{offset}")],
        ]
    )


def level_edit_keyboard(user_id: int, offset: int) -> InlineKeyboardMarkup:
    """أزرار تعديل سريع للمستوى (+/-) بالإضافة لخيار إدخال قيمة مخصصة."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➖ 1", callback_data=f"owner:lvl_sub:{user_id}:{offset}:1"),
                InlineKeyboardButton(text="➕ 1", callback_data=f"owner:lvl_add:{user_id}:{offset}:1"),
            ],
            [
                InlineKeyboardButton(text="➖ 5", callback_data=f"owner:lvl_sub:{user_id}:{offset}:5"),
                InlineKeyboardButton(text="➕ 5", callback_data=f"owner:lvl_add:{user_id}:{offset}:5"),
            ],
            [InlineKeyboardButton(text="✏️ تحديد قيمة مخصصة", callback_data=f"owner:lvl_custom:{user_id}:{offset}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")],
        ]
    )


def balance_edit_keyboard(user_id: int, offset: int) -> InlineKeyboardMarkup:
    """
    أزرار تعديل سريع للرصيد (+/-) بالإضافة لخيار إدخال قيمة مخصصة.
    """
    quick_amounts = [1_000, 5_000, 10_000]

    buttons = []

    for amount in quick_amounts:
        buttons.append([
            InlineKeyboardButton(text=f"➖ {amount:,}", callback_data=f"owner:bal_sub:{user_id}:{offset}:{amount}"),
            InlineKeyboardButton(text=f"➕ {amount:,}", callback_data=f"owner:bal_add:{user_id}:{offset}:{amount}"),
        ])

    buttons.append([InlineKeyboardButton(text="✏️ تحديد قيمة مخصصة", callback_data=f"owner:bal_custom:{user_id}:{offset}")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"owner:member:{user_id}:{offset}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_cancel_keyboard() -> InlineKeyboardMarkup:
    """زر إلغاء أثناء انتظار نص البحث."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:members:0")],
        ]
    )


def search_results_keyboard(results: list[tuple[int, str | None, str]]) -> InlineKeyboardMarkup:
    """نتائج البحث كأزرار (بدون ترقيم صفحات - الحد الأقصى 10)."""
    buttons = []

    for user_id, username, full_name in results:
        label = f"{full_name} | @{username}" if username else full_name
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"owner:member:{user_id}:0")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:members:0")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== لوحة إعدادات المستويات (levels) =====

def levels_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ رسائل المستويات 2-5", callback_data="owner:levels:edit_tier1")],
            [InlineKeyboardButton(text="✏️ رسائل المستوى 6+", callback_data="owner:levels:edit_tier2")],
            [InlineKeyboardButton(text="✏️ مكافأة رفع المستوى", callback_data="owner:levels:edit_reward")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )
