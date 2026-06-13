"""
نصوص "لوحة التحكم".
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


MAIN_MENU_TEXT = "👑 <b>لوحة التحكم</b>\n━━━━━━━━━━━━━━━\nاختر النظام الذي تريد إدارته:"

NO_PERMISSION = "❌ هذا الأمر للمالك فقط."


def moderators_text(admin_count: int, moderator_count: int) -> str:
    return (
        f"👮 <b>نظام الإداريين</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🛡️ الأدمن: {admin_count}\n"
        f"🔧 المشرفين: {moderator_count}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ إدارة الرتب بالتفصيل ستُضاف قريباً."
    )


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
    amounts_display = " / ".join(f"{a:,}" for a in amounts)

    return (
        f"💸 <b>نظام الخصم والمكافأة</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 القيم الحالية: {amounts_display} د.ع\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ تعديل القيم من هنا ستُضاف قريباً."
    )


def cleanup_text(cleanup_range: int) -> str:
    return (
        f"🧹 <b>نظام التنظيف</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔢 عدد الرسائل لكل تنظيف: {cleanup_range}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ تعديل العدد من هنا ستُضاف قريباً."
    )
