"""
نصوص نظام الحظر/الكتم/التحذير.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def duration_label(seconds: int) -> str:
    """يحول عدد الثواني لنص عربي مقروء (مثل '15 دقيقة')."""
    if seconds % 86400 == 0:
        days = seconds // 86400
        return f"{days} يوم" if days == 1 else f"{days} أيام"

    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} ساعة" if hours == 1 else f"{hours} ساعات"

    if seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} دقيقة" if minutes == 1 else f"{minutes} دقائق"

    return f"{seconds} ثانية"


def category_selection_text(action_label: str, replied_text: str | None) -> str:
    lines = []

    if replied_text:
        lines.append(f"💬 الرسالة:\n«{replied_text}»")
        lines.append("━━━━━━━━━━━━━━━")

    lines.append(f"اختر فئة مدة ال{action_label}:")

    return "\n".join(lines)


def duration_selection_text(action_label: str) -> str:
    return f"اختر مدة ال{action_label}:"


def confirm_text(action_label: str, duration_text: str) -> str:
    return (
        f"تأكيد ال{action_label}:\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⏰ المدة: {duration_text}"
    )


def confirm_warn_text(replied_text: str | None) -> str:
    lines = []

    if replied_text:
        lines.append(f"💬 الرسالة:\n«{replied_text}»")
        lines.append("━━━━━━━━━━━━━━━")

    lines.append("تأكيد التحذير؟")

    return "\n".join(lines)


def mute_notification(full_name: str, username: str | None, duration_text: str, reason: str | None, by_full_name: str) -> str:
    username_display = f"@{username}" if username else ""
    reason_display = reason if reason else "-"

    return (
        f"🔇 <b>تم كتم العضو</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"⏰ المدة: {duration_text}\n"
        f"📝 السبب: {reason_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


def ban_notification(full_name: str, username: str | None, duration_text: str, reason: str | None, by_full_name: str) -> str:
    username_display = f"@{username}" if username else ""
    reason_display = reason if reason else "-"

    return (
        f"🚫 <b>تم حظر العضو</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"⏰ المدة: {duration_text}\n"
        f"📝 السبب: {reason_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


def warn_notification(full_name: str, username: str | None, reason: str | None, by_full_name: str) -> str:
    username_display = f"@{username}" if username else ""
    reason_display = reason if reason else "-"

    return (
        f"⚠️ <b>تحذير</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"📝 السبب: {reason_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


def mute_expired_notification(full_name: str, username: str | None) -> str:
    username_display = f"@{username}" if username else ""
    return f"🔇 انتهت مدة كتم {full_name} {username_display}، يمكنه الكتابة الآن."


def ban_expired_notification(full_name: str, username: str | None) -> str:
    username_display = f"@{username}" if username else ""
    return f"🚫 انتهت مدة حظر {full_name} {username_display}."


MUTE_EXPIRED_PRIVATE = "🔇 انتهت مدة كتمك في المجموعة، يمكنك الكتابة الآن."

BAN_EXPIRED_PRIVATE = "🚫 انتهت مدة حظرك في المجموعة."


# ===== رسائل الحالات والأخطاء =====

NO_PERMISSION = "❌ لا تملك الصلاحية لاستخدام هذا الأمر."

NO_REPLY = "❌ يجب الرد على رسالة العضو المطلوب لاستخدام هذا الأمر."

CANCELLED = "❌ تم الإلغاء."
