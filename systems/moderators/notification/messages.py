"""
نصوص نظام الإداريين.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


RANK_NAMES = {
    "member": "عضو",
    "moderator": "مشرف 🔧",
    "admin": "أدمن 🛡️",
    "owner": "المالك 👑",
}


def promotion_notification(full_name: str, username: str | None, new_rank: str, by_full_name: str) -> str:
    """رسالة إشعار المجموعة عند ترقية عضو."""
    username_display = f"@{username}" if username else ""
    rank_display = RANK_NAMES.get(new_rank, new_rank)

    return (
        f"⬆️ <b>ترقية</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"🎖️ الرتبة الجديدة: {rank_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


def demotion_notification(full_name: str, username: str | None, new_rank: str, by_full_name: str) -> str:
    """رسالة إشعار المجموعة عند تخفيض عضو."""
    username_display = f"@{username}" if username else ""
    rank_display = RANK_NAMES.get(new_rank, new_rank)

    return (
        f"⬇️ <b>تخفيض</b>\n"
        f"👤 العضو: {full_name} {username_display}\n"
        f"🎖️ الرتبة الجديدة: {rank_display}\n"
        f"👮 بواسطة: {by_full_name}"
    )


# يظهر إذا حاول عضو عادي استخدام أمر يحتاج صلاحية معينة
NO_PERMISSION = "❌ لا تملك الصلاحية لاستخدام هذا الأمر."

# يظهر عند محاولة ترقية عضو هو بالفعل بأعلى رتبة ممكنة
ALREADY_TOP_RANK = "❌ هذا العضو بالفعل بأعلى رتبة ممكنة (أو هو المالك)."

# يظهر عند محاولة تخفيض عضو رتبته "عضو" بالفعل
ALREADY_MEMBER = "❌ هذا العضو بالفعل رتبته \"عضو\" (أو هو المالك)."
