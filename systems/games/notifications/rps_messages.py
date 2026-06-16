"""
نصوص لعبة حجر ورقة مقص (rps).
"""


PICK_CHOICE_TEXT = "🪨📄✂️ اختر:"


def waiting_challenger_text(owner_name: str) -> str:
    return f"⚔️ {owner_name} اختار! من يتحداه؟"


def winner_text(winner_name: str, loser_name: str, winner_choice: str, loser_choice: str, reward: int) -> str:
    return (
        f"🏆 <b>{winner_name}</b> فاز!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{winner_name}: {winner_choice}\n"
        f"{loser_name}: {loser_choice}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎁 المكافأة: {reward:,} د.ع"
    )


def draw_text(name1: str, name2: str, choice: str) -> str:
    return f"🤝 تعادل! كلاكما اختار {choice}\n({name1} و {name2})"
