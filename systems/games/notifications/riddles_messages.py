"""
نصوص لعبة الألغاز (riddles).
"""


def riddle_text(question: str, timeout: int) -> str:
    return f"🧩 <b>لغز!</b>\n━━━━━━━━━━━━━━━\n{question}\n━━━━━━━━━━━━━━━\n⏳ عندك {timeout} ثوانٍ للجواب"


TIME_UP_TEXT = "⌛ خلص الوقت! ما حليت اللغز بالوكت المحدد."


def correct_answer_text(full_name: str, reward: int) -> str:
    return f"🧠 <b>حليتها!</b>\n🎉 {full_name} ربح {reward:,} د.ع"
