"""
Leaderboard Pro System - نسخة قوية بعد تعديل (الثروة بدل المستوى)
"""

def get_level(balance: int) -> tuple[str, str]:
    if balance >= 1000000:
        return "$", "مليونير"
    elif balance >= 500000:
        return "مطنوخ", "$"
    else:
        return "$", "مطنوخ"


def get_activity(balance: int) -> str:
    if balance >= 50000:
        return "نشط عالي"
    elif balance >= 250000:
        return "نشط"
    else:
        return "عادي"


def leaderboard_text(entries: list[tuple[int, str | None, str, int]]) -> str:
    if not entries:
        return "📊 لا يوجد أعضاء مسجلين حتى الآن."

    medals = {1: "👑", 2: "🥈", 3: "🥉"}

    lines = [
        "🏆 لوحة المتصدرين | نظام الرتب",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for rank, username, full_name, balance in entries:
        medal = medals.get(rank, f"#{rank}")
        level_text, level_icon = get_level(balance)
        activity = get_activity(balance)

        lines.append(f"{medal} {full_name}")
        lines.append(f"🆔 @{username}" if username else "🆔 غير متوفر")

        lines.append("━━━━━━━━━━━━")

        lines.append(f"💰 الرصيد: {balance:,} د.ع")

        # 🔥 التعديل هنا فقط
        lines.append(f"💎 الثروة: {level_text} {level_icon}")

        lines.append(f"📈 الحالة: {activity}")

        lines.append("━━━━━━━━━━━━")
        lines.append("")

    lines.append("⚡ يتم تحديث الترتيب تلقائياً")

    return "\n".join(lines)


INSUFFICIENT_BALANCE = "❌ رصيدك غير كافٍ لإتمام هذه العملية."