"""
نصوص نظام الخصم والمكافأة.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def amount_selection_text(action_label: str, replied_text: str | None) -> str:
    """
    النص الذي يظهر مع أزرار اختيار المبلغ (خصم/مكافأة).
    action_label: "خصم" أو "مكافأة"
    """
    lines = []

    if replied_text:
        lines.append(f"💬 الرسالة:\n«{replied_text}»")
        lines.append("━━━━━━━━━━━━━━━")

    lines.append(f"اختر مبلغ ال{action_label}:")

    return "\n".join(lines)


def ask_reason_text(action_label: str, amount: int) -> str:
    """النص الذي يظهر عند طلب السبب بعد اختيار المبلغ."""
    return (
        f"المبلغ المحدد: {amount:,} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"أرسل سبب ال{action_label}، أو اضغط ⏭️ بدون سبب"
    )


def confirm_text(action_label: str, amount: int, reason: str | None) -> str:
    """النص الذي يظهر عند التأكيد النهائي."""
    reason_display = reason if reason else "بدون سبب"

    return (
        f"تأكيد ال{action_label}:\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 المبلغ: {amount:,} د.ع\n"
        f"📝 السبب: {reason_display}"
    )


def deduct_notification(
    full_name: str,
    username: str | None,
    amount: int,
    reason: str | None,
    by_full_name: str,
) -> str:
    """رسالة إشعار المجموعة عند تنفيذ خصم."""
    username_display = f"@{username}" if username else ""
    reason_display = reason if reason else "-"

    return (
        f"✂️ <b>تم خصم الرصيد</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"💰 المبلغ: {amount:,} د.ع\n"
        f"📝 السبب: {reason_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


def reward_notification(
    full_name: str,
    username: str | None,
    amount: int,
    reason: str | None,
    by_full_name: str,
) -> str:
    """رسالة إشعار المجموعة عند تنفيذ مكافأة."""
    username_display = f"@{username}" if username else ""
    reason_display = reason if reason else "-"

    return (
        f"🎁 <b>تم منح مكافأة</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"💰 المبلغ: {amount:,} د.ع\n"
        f"📝 السبب: {reason_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


# ===== رسائل الحالات والأخطاء =====

NO_PERMISSION = "❌ لا تملك الصلاحية لاستخدام هذا الأمر."

NO_REPLY = "❌ يجب الرد على رسالة العضو المطلوب لاستخدام هذا الأمر."

CANCELLED = "❌ تم الإلغاء."

INSUFFICIENT_BALANCE_FOR_DEDUCT = "❌ رصيد العضو غير كافٍ لهذا الخصم."
