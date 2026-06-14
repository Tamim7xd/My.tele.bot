"""
نصوص لوحتي "مشرف" و"ادمن".
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def main_menu_text(violators_count: int) -> str:
    return (
        f"📋 <b>لوحة الإدارة</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔴 المخالفون: {violators_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط لعرض قائمة المخالفين:"
    )


def violators_list_text(total: int) -> str:
    if total == 0:
        return "📋 <b>قائمة المخالفين</b>\n━━━━━━━━━━━━━━━\nلا يوجد أعضاء مخالفون حالياً. 🎉"

    return f"📋 <b>قائمة المخالفين</b> ({total})\n━━━━━━━━━━━━━━━\nاختر عضواً:"


def member_page_text(
    full_name: str,
    username: str | None,
    violations_count: int,
    warnings_count: int,
    is_muted: bool,
    is_banned: bool,
) -> str:
    username_display = f"@{username}" if username else "بدون يوزر"

    status_lines = []
    if is_muted:
        status_lines.append("🔇 مكتوم حالياً")
    if is_banned:
        status_lines.append("🚫 محظور حالياً")

    status_block = ("\n".join(status_lines) + "\n") if status_lines else ""

    return (
        f"👤 <b>{full_name}</b> | {username_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📋 المخالفات: {violations_count}\n"
        f"⚠️ التحذيرات: {warnings_count}\n"
        f"{status_block}"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر إجراءً:"
    )


# ===== فتح الكتم =====

UNMUTE_SUCCESS = "🔊 تم فتح الكتم عن العضو."

NOT_MUTED = "❌ هذا العضو غير مكتوم حالياً."


# ===== تمديد الكتم =====

def extend_mute_category_text(full_name: str) -> str:
    return f"⏳ <b>تمديد كتم {full_name}</b>\n━━━━━━━━━━━━━━━\nاختر فئة المدة:"


def extend_mute_list_text(full_name: str) -> str:
    return f"⏳ تمديد كتم {full_name}\n━━━━━━━━━━━━━━━\nاختر المدة الإضافية:"


def extend_mute_success(full_name: str, duration_text: str) -> str:
    return f"⏳ تم تمديد كتم {full_name} بـ {duration_text} إضافية."


# ===== إلغاء الحظر (أدمن فقط) =====

UNBAN_SUCCESS = "✅ تم إلغاء الحظر عن العضو."

NOT_BANNED = "❌ هذا العضو غير محظور حالياً."


# ===== تخفيض التحذيرات =====

def reduce_warning_success(full_name: str, new_count: int) -> str:
    return f"⬇️ تم تخفيض تحذيرات {full_name}. التحذيرات الحالية: {new_count}"


REDUCE_WARNING_NONE = "❌ لا يوجد تحذيرات لهذا العضو لتخفيضها."


# ===== صلاحيات =====

NO_PERMISSION_SILENT = ""  # صمت تام - لا نص يُستخدم
