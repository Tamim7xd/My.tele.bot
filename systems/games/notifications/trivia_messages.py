"""
نصوص لعبة الأسئلة المرحة (trivia).
"""


def question_text(question: str, timeout: int) -> str:
    return f"🧠 <b>سؤال!</b>\n━━━━━━━━━━━━━━━\n{question}\n━━━━━━━━━━━━━━━\n⏳ عندك {timeout} ثوانٍ للجواب"


TIME_UP_TEXT = "⌛ خلص الوقت! ما جاوبت بالوكت المحدد."


def correct_answer_text(full_name: str, reward: int) -> str:
    return f"✅ <b>إجابة صحيحة!</b>\n🎉 {full_name} ربح {reward:,} د.ع"

WRONG_ANSWER_TEXT = "❌ إجابة خاطئة! انتهت اللعبة."
