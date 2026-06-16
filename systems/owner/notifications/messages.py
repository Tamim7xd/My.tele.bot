"""
نصوص "لوحة التحكم".
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


MAIN_MENU_TEXT = "👑 <b>لوحة التحكم</b>\n━━━━━━━━━━━━━━━\nاختر النظام الذي تريد إدارته:"

NO_PERMISSION = "❌ هذا الأمر للمالك فقط."

CANCELLED = "❌ تم الإلغاء."


def moderators_text(admin_count: int, moderator_count: int) -> str:
    return (
        f"👮 <b>نظام الإداريين</b>\n"
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
        return f"{icon} <b>{rank_display}</b>\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء بهذه الرتبة حالياً."

    return f"{icon} <b>{rank_display}</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً:"


def staff_member_text(full_name: str, username: str | None, rank: str) -> str:
    username_display = f"@{username}" if username else "بدون يوزر"
    rank_display = RANK_NAMES.get(rank, rank)

    return (
        f"👤 <b>{full_name}</b> | {username_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎖️ الرتبة: {rank_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إجراءً:"
    )


def permissions_text(full_name: str, rank: str) -> str:
    rank_display = RANK_NAMES.get(rank, rank)

    return (
        f"⚙️ <b>صلاحيات {full_name}</b>\n"
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
        f"💰 <b>نظام الرصيد</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 إجمالي الرصيد المتداول: {total_balance:,} د.ع\n"
        f"🏆 عدد المتصدرين: {top_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ تعديل قيم الرصيد بالتفصيل ستُضاف قريباً."
    )


def rewards_text(amounts: list[int]) -> str:
    return (
        f"💸 <b>نظام الخصم والمكافأة</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"القيم الحالية أدناه. اضغط 🗑️ للحذف، أو ➕ للإضافة:"
    )


def cleanup_text(cleanup_range: int) -> str:
    return (
        f"🧹 <b>نظام التنظيف</b>\n"
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
        return "👥 <b>الأعضاء</b>\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء مسجلين حتى الآن."

    return f"👥 <b>الأعضاء</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً، أو استخدم 🔍 البحث:"


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
        f"👤 <b>{full_name}</b> | {username_display}\n"
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
        f"💰 <b>تعديل رصيد {full_name}</b>\n"
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
        f"📊 <b>تعديل مستوى {full_name}</b>\n"
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
    return f"🔇 <b>كتم {full_name}</b>\n━━━━━━━━━━━━━━━\nاختر فئة المدة:"


def member_ban_category_text(full_name: str) -> str:
    return f"🚫 <b>حظر {full_name}</b>\n━━━━━━━━━━━━━━━\nاختر فئة المدة:"


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
        f"📊 <b>نظام المستويات</b>\n"
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

