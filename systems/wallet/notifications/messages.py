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

    lines = ["💰 الأكثر رصيداً", "━━━━━━━━━━━━━━━", ""]

    for rank, username, full_name, balance in entries:
        medal = medals.get(rank, f"{rank}.")

        # الاسم + اليوزر
        if username:
            lines.append(f"{medal} {full_name} (@{username})")
        else:
            lines.append(f"{medal} {full_name}")

        # الرصيد
        lines.append(f"💵 {balance:,} د.ع")

        # فراغ بين كل عضو
        lines.append("")

    return "\n".join(lines)


# يظهر إذا حاول عضو تحويل/استخدام مبلغ أكبر من رصيده
INSUFFICIENT_BALANCE = "❌ رصيدك غير كافٍ لإتمام هذه العملية."