"""
نصوص نظام الأعضاء.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def account_card_text(
    full_name: str,
    username: str | None,
    level: int,
    messages_count: int,
    balance: int,
    warnings_count: int,
    violations_count: int,
    games_played: int,
    games_won: int,
) -> str:
    """
    يبني نص بطاقة الحساب التي تظهر عند كتابة "حساب" أو مرادفاتها.
    """
    username_display = f"@{username}" if username else "بدون يوزر"

    return (
        f"👤 <b>{full_name}</b> | {username_display}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 المستوى: {level}\n"
        f"💬 الرسائل: {messages_count}\n"
        f"💰 الرصيد: {balance:,} د.ع\n"
        f"⚠️ التحذيرات: {warnings_count}\n"
        f"📋 المخالفات: {violations_count}\n"
        f"🎮 اللعب: {games_played} | الفوز: {games_won}"
    )


# نص يظهر إذا حاول عضو عادي عرض حساب عضو آخر
NO_PERMISSION_VIEW_OTHERS = "❌ هذا الأمر متاح فقط للأدمن والمشرف عند الرد على عضو."
