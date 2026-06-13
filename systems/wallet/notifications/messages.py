"""
نصوص نظام الرصيد.
تعديل أي نص هنا لا يؤثر على أي نظام آخر.
"""


def leaderboard_text(entries: list[tuple[int, str | None, str, int]]) -> str:
    """
    يبني نص قائمة الترتيب (الأكثر رصيداً).

    entries: قائمة من (الترتيب, اليوزر, الاسم, الرصيد)
    """
    if not entries:
        return "📊 لا يوجد أعضاء مسجلين حتى الآن."

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    lines = ["💰 <b>الأكثر رصيداً</b>", "━━━━━━━━━━━━━━━"]

    for rank, username, full_name, balance in entries:
        medal = medals.get(rank, f"{rank}.")
        username_display = f"@{username}" if username else ""
        lines.append(f"{medal} {full_name} {username_display} — {balance:,} د.ع")

    return "\n".join(lines)


# يظهر إذا حاول عضو تحويل/استخدام مبلغ أكبر من رصيده
INSUFFICIENT_BALANCE = "❌ رصيدك غير كافٍ لإتمام هذه العملية."
