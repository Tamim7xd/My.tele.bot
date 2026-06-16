"""
نصوص "لوحة التحكم".
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""

MAIN_MENU_TEXT = "👑 **لوحة التحكم**\n━━━━━━━━━━━━━━━\nاختر النظام الذي تريد إدارته:"

NO_PERMISSION = "❌ هذا الأمر للمالك فقط."

CANCELLED = "❌ تم الإلغاء."


def moderators_text(admin_count: int, moderator_count: int) -> str:
    return (
        f"👮 **نظام الإداريين**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🛡️ الأدمن: {admin_count}\n"
        f"🔧 المشرفين: {moderator_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر فئة لعرض الأعضاء:"
    )


RANK_NAMES = {
    "member": "عضو",
    "moderator": "مشرف 🔧",
    "admin": "أدمن 🛡️",
    "owner": "المالك 👑",
}


def staff_list_text(rank: str, total: int) -> str:
    rank_display = RANK_NAMES.get(rank, rank)
    icon = "🛡️" if rank == "admin" else "🔧"

    if total == 0:
        return f"{icon} **{rank_display}**\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء بهذه الرتبة حالياً."

    return f"{icon} **{rank_display}** ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً:"


def staff_member_text(full_name: str, username: str | None, rank: str) -> str:
    username_display = f"@{username}" if username else "بدون يوزر"
    rank_display = RANK_NAMES.get(rank, rank)

    return (
        f"👤 **{full_name}** | {username_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎖️ الرتبة: {rank_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إجراءً:"
    )


def permissions_text(full_name: str, rank: str) -> str:
    rank_display = RANK_NAMES.get(rank, rank)

    return (
        f"⚙️ **صلاحيات {full_name}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"الرتبة: {rank_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط على أي صلاحية لتفعيلها أو إيقافها:"
    )


def promoted_text(full_name: str, new_rank: str) -> str:
    rank_display = RANK_NAMES.get(new_rank, new_rank)
    return f"⬆️ تم ترقية {full_name} إلى {rank_display}"


def demoted_text(full_name: str, new_rank: str) -> str:
    rank_display = RANK_NAMES.get(new_rank, new_rank)
    return f"⬇️ تم تخفيض {full_name} إلى {rank_display}"


def wallet_text(total_balance: int, top_count: int) -> str:
    return (
        f"💰 **نظام الرصيد**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 إجمالي الرصيد المتداول: {total_balance:,} د.ع\n"
        f"🏆 عدد المتصدرين: {top_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ تعديل قيم الرصيد بالتفصيل ستُضاف قريباً."
    )


def rewards_text(amounts: list[int]) -> str:
    return (
        f"💸 **نظام الخصم والمكافأة**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"القيم الحالية أدناه. اضغط 🗑️ للحذف، أو ➕ للإضافة:"
    )


def cleanup_text(cleanup_range: int) -> str:
    return (
        f"🧹 **نظام التنظيف**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔢 عدد الرسائل لكل تنظيف: {cleanup_range}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط ✏️ لتعديل العدد."
    )


CLEANUP_EDIT_PROMPT = "✏️ أرسل العدد الجديد لرسائل التنظيف (رقم صحيح موجب)."

CLEANUP_EDIT_INVALID = "❌ يجب إرسال رقم صحيح موجب."


def cleanup_updated_text(cleanup_range: int) -> str:
    return f"✅ تم تحديث عدد رسائل التنظيف إلى: {cleanup_range}"


# ===== نصوص نظام الأعضاء =====

def members_list_text(total: int) -> str:
    if total == 0:
        return "👥 **الأعضاء**\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء مسجلين حتى الآن."

    return f"👥 **الأعضاء** ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً، أو استخدم 🔍 البحث:"


def member_page_text(
    full_name: str,
    username: str | None,
    rank: str,
    level: int,
    messages_count: int,
    balance: int,
    is_muted: bool = False,
    is_banned: bool = False,
) -> str:
    username_display = f"@{username}" if username else "بدون يوزر"
    rank_display = RANK_NAMES.get(rank, rank)

    status_lines = []
    if is_muted:
        status_lines.append("🔇 مكتوم حالياً")
    if is_banned:
        status_lines.append("🚫 محظور حالياً")

    status_block = ("\n".join(status_lines) + "\n") if status_lines else ""

    return (
        f"👤 **{full_name}** | {username_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎖️ الرتبة: {rank_display}\n"
        f"📊 المستوى: {level}\n"
        f"💬 الرسائل: {messages_count}\n"
        f"💰 الرصيد: {balance:,} د.ع\n"
        f"{status_block}"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إجراءً:"
    )


def balance_edit_text(full_name: str, balance: int) -> str:
    return (
        f"💰 **تعديل رصيد {full_name}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"الرصيد الحالي: {balance:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إضافة/خصم سريع، أو حدد قيمة مخصصة:"
    )


BALANCE_CUSTOM_PROMPT = "✏️ أرسل الرصيد الجديد (رقم صحيح، 0 أو أكبر)."

BALANCE_CUSTOM_INVALID = "❌ يجب إرسال رقم صحيح 0 أو أكبر."


def balance_updated_text(full_name: str, new_balance: int) -> str:
    return f"✅ تم تحديث رصيد {full_name} إلى: {new_balance:,} د.ع"


MEMBER_SEARCH_PROMPT = "🔍 أرسل اسم أو يوزر العضو للبحث عنه."

MEMBER_SEARCH_NO_RESULTS = "❌ لم يتم العثور على أي عضو مطابق."


# ===== نصوص نظام الخصم والمكافأة (المرنة) =====

REWARD_AMOUNT_ADD_PROMPT = "➕ أرسل القيمة الجديدة (رقم صحيح موجب) لإضافتها لقائمة الخصم/المكافأة."

REWARD_AMOUNT_ADD_INVALID = "❌ يجب إرسال رقم صحيح موجب."

REWARD_AMOUNT_ADD_DUPLICATE = "❌ هذه القيمة موجودة بالفعل في القائمة."

REWARD_AMOUNT_MIN_REACHED = "❌ يجب أن تبقى قيمة واحدة على الأقل في القائمة."


def reward_amount_added_text(amounts: list[int]) -> str:
    amounts_display = " / ".join(f"{a:,}" for a in amounts)
    return f"✅ تمت الإضافة. القيم الحالية: {amounts_display} د.ع"


def reward_amount_removed_text(amounts: list[int]) -> str:
    amounts_display = " / ".join(f"{a:,}" for a in amounts)
    return f"🗑️ تم الحذف. القيم الحالية: {amounts_display} د.ع"


# ===== نصوص تعديل المستوى =====

def level_edit_text(full_name: str, level: int) -> str:
    return (
        f"📊 **تعديل مستوى {full_name}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"المستوى الحالي: {level}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إضافة/خصم سريع، أو حدد قيمة مخصصة:"
    )


LEVEL_CUSTOM_PROMPT = "✏️ أرسل المستوى الجديد (رقم صحيح، 1 أو أكبر)."

LEVEL_CUSTOM_INVALID = "❌ يجب إرسال رقم صحيح 1 أو أكبر."


def level_updated_text(full_name: str, new_level: int) -> str:
    return f"✅ تم تحديث مستوى {full_name} إلى: {new_level}"


# ===== نصوص moderation من اللوحة =====

def member_mute_category_text(full_name: str) -> str:
    return f"🔇 **كتم {full_name}**\n━━━━━━━━━━━━━━━\nاختر فئة المدة:"


def member_ban_category_text(full_name: str) -> str:
    return f"🚫 **حظر {full_name}**\n━━━━━━━━━━━━━━━\nاختر فئة المدة:"


def member_duration_list_text(full_name: str, action_label: str) -> str:
    return f"{action_label} {full_name}\n━━━━━━━━━━━━━━━\nاختر المدة:"


def member_warn_confirm_text(full_name: str) -> str:
    return f"⚠️ تأكيد تحذير {full_name}؟"


def member_mute_applied_text(full_name: str, duration_text: str) -> str:
    return f"🔇 تم كتم {full_name} لمدة {duration_text}"


def member_ban_applied_text(full_name: str, duration_text: str) -> str:
    return f"🚫 تم حظر {full_name} لمدة {duration_text}"


def member_unmute_applied_text(full_name: str) -> str:
    return f"🔊 تم رفع الكتم عن {full_name}"


def member_unban_applied_text(full_name: str) -> str:
    return f"✅ تم رفع الحظر عن {full_name}"


def member_warn_applied_text(full_name: str) -> str:
    return f"⚠️ تم تحذير {full_name}"


# ===== نصوص لوحة الإعدادات: المستويات =====

def levels_settings_text(tier_1_5: int, tier_6_plus: int, reward: int) -> str:
    return (
        f"📊 **نظام المستويات**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📈 المستويات 2-5: {tier_1_5} رسالة لكل مستوى\n"
        f"📈 المستوى 6+: {tier_6_plus} رسالة لكل مستوى\n"
        f"🎁 مكافأة رفع المستوى: {reward:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )


LEVELS_EDIT_TIER_1_5_PROMPT = "✏️ أرسل عدد الرسائل المطلوب لكل مستوى (2-5)."

LEVELS_EDIT_TIER_6_PLUS_PROMPT = "✏️ أرسل عدد الرسائل المطلوب لكل مستوى (6 فأكثر)."

LEVELS_EDIT_REWARD_PROMPT = "✏️ أرسل قيمة مكافأة رفع المستوى الجديدة."

LEVELS_EDIT_INVALID = "❌ يجب إرسال رقم صحيح موجب."


def levels_updated_text(tier_1_5: int, tier_6_plus: int, reward: int) -> str:
    return (
        f"✅ تم التحديث:\n"
        f"📈 المستويات 2-5: {tier_1_5} رسالة\n"
        f"📈 المستوى 6+: {tier_6_plus} رسالة\n"
        f"🎁 المكافأة: {reward:,} د.ع"
    )


# ═══════════════════════════════════════
# ═══ نصوص نظام العضويات الإدارية ═══
# ═══════════════════════════════════════

RANK_NAMES_NEW = {
    "owner": "👑 المالك",
    "admin": "🔥 الأدمن",
    "moderator": "⚡ المشرف",
    "member": "👤 العضو",
}


def ranks_main_text(ranks: list) -> str:
    """نص القائمة الرئيسية للعضويات"""
    text = "👑 **إدارة العضويات الإدارية**\n━━━━━━━━━━━━━━━\n"
    text += "📊 **الترتيب الهرمي:** (الرقم الأصغر = أعلى صلاحية)\n\n"
    
    for rank in ranks:
        protected = "🔒" if rank['is_protected'] else ""
        perms_count = len(rank['permissions']) if rank['permissions'] else 0
        text += f"{rank['icon']} **{rank['display_name']}** {protected}\n"
        text += f"├ المستوى: {rank['level']}\n"
        text += f"├ الصلاحيات: {perms_count}\n"
        text += f"└ اللون: `{rank['color']}`\n\n"
    
    return text


def ranks_main_keyboard(ranks: list) -> InlineKeyboardMarkup:
    """لوحة القائمة الرئيسية للعضويات"""
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    for rank in ranks:
        protected = "🔒" if rank['is_protected'] else ""
        builder.button(
            text=f"{protected} {rank['icon']} {rank['display_name']}",
            callback_data=f"owner:rank:view:{rank['id']}"
        )
    
    builder.button(text="➕ إضافة عضوية جديدة", callback_data="owner:rank:add")
    builder.button(text="🔙 رجوع للوحة التحكم", callback_data="owner:main")
    builder.adjust(1)
    
    return builder.as_markup()


def rank_details_text(rank: dict, all_perms: list, rank_perms: list) -> str:
    """نص تفاصيل عضوية"""
    cat_names = {
        'moderation': '🛡️ الإشراف',
        'systems': '⚙️ الأنظمة',
        'admin': '⚙️ الإدارة',
        'economy': '💰 الاقتصاد',
        'content': '📝 المحتوى',
        'special': '⭐ خاص'
    }
    
    text = f"{rank['icon']} **{rank['display_name']}**\n\n"
    text += f"📋 **المعلومات:**\n"
    text += f"├ الاسم التقني: `{rank['name']}`\n"
    text += f"├ المستوى: {rank['level']}\n"
    text += f"├ اللون: `{rank['color']}`\n"
    text += f"├ الأيقونة: {rank['icon']}\n"
    text += f"└ محمية: {'نعم 🔒' if rank['is_protected'] else 'لا'}\n\n"
    
    text += f"⚡ **الصلاحيات ({len(rank_perms)}):**\n"
    
    # تجميع حسب التصنيف
    categories = {}
    for perm in all_perms:
        cat = perm['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(perm)
    
    for cat_name, perms in categories.items():
        cat_perms = [p for p in perms if p['code'] in rank_perms]
        if cat_perms:
            emoji = cat_names.get(cat_name, '📌')
            text += f"\n{emoji} **{cat_name.upper()}:**\n"
            for perm in cat_perms:
                text += f"  ✓ {perm['icon']} {perm['display_name']}\n"
    
    return text


def rank_details_keyboard(rank: dict) -> InlineKeyboardMarkup:
    """لوحة تفاصيل عضوية"""
    builder = InlineKeyboardBuilder()
    
    if not rank['is_protected']:
        builder.button(text="✏️ تعديل", callback_data=f"owner:rank:edit:{rank['id']}")
        builder.button(text="⚡ الصلاحيات", callback_data=f"owner:rank:perms:{rank['id']}")
        builder.button(text="🗑️ حذف", callback_data=f"owner:rank:delete:{rank['id']}")
    
    builder.button(text="🔙 رجوع للقائمة", callback_data="owner:ranks")
    builder.adjust(1)
    
    return builder.as_markup()


# ─── إضافة عضوية ───

RANK_ADD_NAME_PROMPT = (
    "➕ **إضافة عضوية إدارية جديدة**\n\n"
    "📝 **الخطوة 1/5:** أرسل الاسم التقني (بالإنجليزية)\n"
    "مثال: `super_mod` أو `helper`\n\n"
    "⚠️ هذا الاسم يُستخدم داخلياً ولا يُعرض للأعضاء."
)

RANK_ADD_NAME_INVALID = "❌ الاسم يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط"

RANK_ADD_NAME_EXISTS = "❌ هذا الاسم مستخدم بالفعل!"

RANK_ADD_DISPLAY_PROMPT = (
    "✅ تم حفظ الاسم التقني\n\n"
    "📝 **الخطوة 2/5:** أرسل الاسم المعروض (بالعربية)\n"
    "مثال: `🌟 المساعد المميز`"
)


def rank_add_level_prompt(ranks: list) -> str:
    """نطلب المستوى الهرمي"""
    text = "📊 **الخطوة 3/5:** اختر المستوى الهرمي\n\n"
    text += "🔢 **المستويات الحالية:**\n"
    for r in ranks:
        text += f"  المستوى {r['level']}: {r['display_name']}\n"
    
    text += "\n✏️ أرسل رقم المستوى الجديد (1-100):\n"
    text += "💡 **ملاحظة:** الرقم الأصغر = أعلى صلاحية"
    return text


RANK_ADD_LEVEL_INVALID = "❌ أرسل رقم صحيح بين 1 و 100"


def rank_add_level_exists(level: int, existing: list) -> str:
    """المستوى مستخدم"""
    available = [l for l in range(1, 101) if l not in existing][:15]
    return (
        f"⚠️ المستوى {level} مستخدم!\n"
        f"المستويات المتاحة: {available}\n"
        f"أرسل مستوى آخر:"
    )


RANK_ADD_COLOR_PROMPT = (
    "🎨 **الخطوة 4/5:** اختر لون العضوية\n\n"
    "أرسل كود HEX أو اختر من القائمة:"
)

RANK_ADD_ICON_PROMPT = (
    "🎯 **الخطوة 5/5:** اختر أيقونة العضوية\n\n"
    "أرسل إيموجي واحد:"
)

RANK_ADD_ICON_INVALID = "❌ أرسل إيموجي واحد فقط!"


def rank_add_permissions_text(display_name: str) -> str:
    """نطلب اختيار الصلاحيات"""
    return (
        f"✅ **تم إنشاء العضوية!**\n\n"
        f"🎯 **{display_name}**\n"
        f"الآن اختر الصلاحيات:"
    )


# ─── تعديل عضوية ───

def rank_edit_text(rank: dict) -> str:
    """نص تعديل عضوية"""
    return (
        f"✏️ **تعديل: {rank['display_name']}**\n\n"
        f"اختر ما تريد تعديله:"
    )


def rank_edit_keyboard(rank_id: int) -> InlineKeyboardMarkup:
    """لوحة تعديل عضوية"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✏️ تعديل الاسم", callback_data=f"owner:rank:edit_name:{rank_id}")
    builder.button(text="🎨 تعديل اللون", callback_data=f"owner:rank:edit_color:{rank_id}")
    builder.button(text="🎯 تعديل الأيقونة", callback_data=f"owner:rank:edit_icon:{rank_id}")
    builder.button(text="⚡ الصلاحيات", callback_data=f"owner:rank:perms:{rank_id}")
    builder.button(text="🔙 رجوع", callback_data=f"owner:rank:view:{rank_id}")
    builder.adjust(1)
    
    return builder.as_markup()


RANK_EDIT_NAME_PROMPT = "✏️ **تغيير الاسم المعروض**\n\nأرسل الاسم الجديد:"

RANK_EDIT_NAME_SUCCESS = "✅ تم تعديل الاسم بنجاح!"


# ─── صلاحيات ───

def rank_permissions_text(rank: dict, current_perms: list) -> str:
    """نص صلاحيات عضوية"""
    return (
        f"⚡ **صلاحيات: {rank['display_name']}**\n\n"
        f"الصلاحيات الحالية: {len(current_perms)}\n\n"
        f"اختر الصلاحيات:"
    )


def permissions_selector_keyboard(rank_id: int, current_perms: list, all_perms: list) -> InlineKeyboardMarkup:
    """محدد الصلاحيات"""
    builder = InlineKeyboardBuilder()
    
    # تجميع حسب التصنيف
    categories = {}
    for perm in all_perms:
        cat = perm['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(perm)
    
    cat_names = {
        'moderation': '🛡️ الإشراف',
        'systems': '⚙️ الأنظمة',
        'admin': '⚙️ الإدارة',
        'economy': '💰 الاقتصاد',
        'content': '📝 المحتوى',
        'special': '⭐ خاص'
    }
    
    for cat_name, perms in categories.items():
        display = cat_names.get(cat_name, cat_name)
        builder.button(text=f"─── {display} ───", callback_data="ignore")
        
        for perm in perms:
            is_active = perm['code'] in current_perms
            check = "✅" if is_active else "⬜"
            builder.button(
                text=f"{check} {perm['icon']} {perm['display_name']}",
                callback_data=f"owner:rank:toggle_perm:{rank_id}:{perm['code']}"
            )
    
    builder.button(text="💾 حفظ الصلاحيات", callback_data=f"owner:rank:save_perms:{rank_id}")
    builder.button(text="🔙 رجوع", callback_data=f"owner:rank:view:{rank_id}")
    builder.adjust(1)
    
    return builder.as_markup()


def rank_permissions_saved(rank: dict, perms: list) -> str:
    """تم حفظ الصلاحيات"""
    return (
        f"💾 **تم حفظ الصلاحيات!**\n\n"
        f"{rank['icon']} {rank['display_name']}\n"
        f"الصلاحيات: {len(perms)}"
    )


def back_to_rank_keyboard(rank_id: int) -> InlineKeyboardMarkup:
    """رجوع لصفحة العضوية"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع للعضوية", callback_data=f"owner:rank:view:{rank_id}")
    return builder.as_markup()


# ─── حذف ───

def rank_delete_confirm_text(rank: dict) -> str:
    """تأكيد حذف"""
    return (
        f"⚠️ **تأكيد الحذف**\n\n"
        f"هل تريد حذف: {rank['icon']} {rank['display_name']}؟\n\n"
        f"❌ **تحذير:** الأعضاء بهذه العضوية سيتم نقلهم للعضو العادي!"
    )


def rank_delete_confirm_keyboard(rank_id: int) -> InlineKeyboardMarkup:
    """تأكيد الحذف"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ نعم، احذف", callback_data=f"owner:rank:confirm_delete:{rank_id}")
    builder.button(text="❌ لا، تراجع", callback_data=f"owner:rank:view:{rank_id}")
    builder.adjust(2)
    return builder.as_markup()


RANK_DELETE_SUCCESS = (
    "✅ **تم حذف العضوية!**\n"
    "تم نقل الأعضاء للعضوية العادية."
)


def back_to_ranks_keyboard() -> InlineKeyboardMarkup:
    """رجوع للقائمة"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع للعضويات", callback_data="owner:ranks")
    return builder.as_markup()


# ─── إشعارات المجموعة ───

def group_promoted_text(user_id: int, old_rank: str, new_rank: str) -> str:
    """ترقية"""
    return f"⬆️ تم ترقية العضو إلى {new_rank} 🎉"

def group_demoted_text(user_id: int, old_rank: str, new_rank: str) -> str:
    """تخفيض"""
    return f"⬇️ تم تخفيض العضو إلى {new_rank}"

def group_rank_changed_text(user_id: int, old_rank: str, new_rank: str) -> str:
    """تغيير عام"""
    return f"🔄 تم تغيير عضوية العضو من {old_rank} إلى {new_rank}"


# ─── أزرار مساعدة ───

def cancel_keyboard() -> InlineKeyboardMarkup:
    """إلغاء"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ إلغاء", callback_data="owner:ranks")
    return builder.as_markup()


def colors_keyboard() -> InlineKeyboardMarkup:
    """ألوان جاهزة"""
    builder = InlineKeyboardBuilder()
    
    colors = [
        ("🔴 أحمر", "#FF4444"),
        ("🟢 أخضر", "#44FF44"),
        ("🔵 أزرق", "#4444FF"),
        ("🟡 أصفر", "#FFFF44"),
        ("🟣 بنفسجي", "#AA44FF"),
        ("🟠 برتقالي", "#FF8844"),
        ("⚪ فضي", "#C0C0C0"),
        ("🌟 ذهبي", "#FFD700"),
        ("⚫ أسود", "#333333"),
        ("🩷 وردي", "#FF69B4"),
    ]
    
    for name, code in colors:
        builder.button(text=name, callback_data=f"owner:rank:color:{code}")
    
    builder.button(text="❌ إلغاء", callback_data="owner:ranks")
    builder.adjust(2)
    
    return builder.as_markup()


def icons_keyboard() -> InlineKeyboardMarkup:
    """أيقونات جاهزة"""
    builder = InlineKeyboardBuilder()
    
    icons = ["👤", "⭐", "🌟", "💎", "🏆", "👑", "🎖️", "🛡️", "⚔️", "🔥", 
             "⚡", "🎯", "🚀", "💪", "🦁", "🦅", "🐉", "❤️", "💚", "💙"]
    
    for icon in icons:
        builder.button(text=icon, callback_data=f"owner:rank:icon:{icon}")
    
    builder.button(text="❌ إلغاء", callback_data="owner:ranks")
    builder.adjust(5)
    
    return builder.as_markup()
