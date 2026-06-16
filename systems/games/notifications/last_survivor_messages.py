"""
نصوص الناجي الأخير (last_survivor).
"""


def announcement_text(fee: int, join_window: int) -> str:
    return (
        f"🧟 <b>بدأت لعبة الناجي الأخير!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 رسوم الدخول: {fee:,} د.ع\n"
        f"⏳ عندكم {join_window} ثانية للانضمام\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اضغط 🙋 انضم للمشاركة!"
    )


ALREADY_JOINED = "✅ أنت مشترك بالفعل!"

INSUFFICIENT_BALANCE = "❌ رصيدك ما يكفي لرسوم الدخول."

JOINED_SUCCESS = "✅ انضممت للعبة!"


def cancelled_text(joined_count: int, min_players: int) -> str:
    return (
        f"❌ <b>تم إلغاء اللعبة</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"عدد المنضمين ({joined_count}) أقل من الحد الأدنى ({min_players}).\n"
        f"تم إرجاع الرسوم لكل من دفع."
    )


def starting_text(player_count: int) -> str:
    return f"🔒 خلص وقت الانضمام! عدد اللاعبين: {player_count}\n🎲 بداية الحذف..."


def elimination_progress_text(eliminated_name: str, remaining_count: int, log: list[str]) -> str:
    log_text = "\n".join(f"💀 {name}" for name in log)

    return (
        f"🧟 <b>الناجي الأخير</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{log_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 المتبقي: {remaining_count}"
    )


def winner_text(winner_name: str, pot: int) -> str:
    return (
        f"🎉 <b>الناجي الأخير: {winner_name}!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 ربح كامل الوعاء: {pot:,} د.ع"
    )
