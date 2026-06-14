"""
نظام الرصيد - نسخة VIP متطورة
توليد لوحة المتصدرين بشكل احترافي
"""

def get_level(balance: int) -> str:
    """
    تحديد مستوى الرصيد (VIP / متوسط / منخفض)
    """
    if balance >= 50000:
        return "🟢 VIP"
    elif balance >= 20000:
        return "🟡 متوسط"
    else:
        return "🔴 منخفض"


def leaderboard_text(entries: list[tuple[int, str | None, str, int]]) -> str:
    """
    بناء قائمة المتصدرين بشكل احترافي

    entries: (الترتيب, اليوزر, الاسم, الرصيد)
    """
    if not entries:
        return "📊 لا يوجد أعضاء مسجلين حتى الآن."

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    lines = [
        "💰 الأكثر رصيداً",
        "━━━━━━━━━━━━━━━",
        ""
    ]

    for rank, username, full_name, balance in entries:
        medal = medals.get(rank, f"{rank}.")
        level = get_level(balance)

        # الاسم + اليوزر
        if username:
            lines.append(f"{medal} {full_name} (@{username})")
        else:
            lines.append(f"{medal} {full_name}")

        # المستوى + الرصيد
        lines.append(f"{level} | الرصيد: {balance:,} د.ع")

        # فاصل أنيق بين كل عضو
        lines.append("━━━━━━━━━━━━━━━")

    return "\n".join(lines)


# نص ثابت عند عدم كفاية الرصيد
INSUFFICIENT_BALANCE = "❌ رصيدك غير كافٍ لإتمام هذه العملية."