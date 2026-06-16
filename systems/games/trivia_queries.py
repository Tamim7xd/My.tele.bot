"""
لعبة الأسئلة المرحة (trivia) - استعلامات/تخزين الأسئلة والإعدادات.

الأسئلة تُخزَّن في settings تحت مفتاح "trivia_questions" كقائمة:
[{"question": "...", "answers": ["جواب1", "جواب2", ...], "reward": 1000}, ...]

answers: قائمة بكل الصيغ المقبولة للجواب الصحيح (تُطبَّع عند المقارنة
عبر نفس محرك التطبيع المستخدم في نظام الحماية، لفهم صيغ الكتابة المختلفة).
"""

import asyncpg

from core.database import get_setting, set_setting


TRIVIA_QUESTIONS_KEY = "trivia_questions"
TRIVIA_TIMEOUT_KEY = "trivia_timeout_seconds"
DEFAULT_TRIVIA_TIMEOUT = 5


DEFAULT_QUESTIONS = [
    {
        "question": "شلون تقول لأمك إنك جوعان بالعراقي؟ 😂",
        "answers": ["جوعان", "متخبل من الجوع", "ماتت روحي", "اموت"],
        "reward": 1000,
    },
    {
        "question": "شنو اسم الأكلة اللي فيها رز ودجاج وتعتبر ملكة الأكل العراقي؟",
        "answers": ["برياني", "البرياني"],
        "reward": 1000,
    },
    {
        "question": "وين تروح لو حد قالك (نطيها بالعافية)؟",
        "answers": ["مطعم", "العزومة", "اكل", "وليمة", "بيت احد", "ضيافة"],
        "reward": 1000,
    },
]


async def get_questions(pool: asyncpg.Pool) -> list[dict]:
    return await get_setting(pool, TRIVIA_QUESTIONS_KEY, DEFAULT_QUESTIONS)


async def set_questions(pool: asyncpg.Pool, questions: list[dict]) -> None:
    await set_setting(pool, TRIVIA_QUESTIONS_KEY, questions)


async def add_question(pool: asyncpg.Pool, question: str, answers: list[str], reward: int) -> None:
    questions = await get_questions(pool)
    questions.append({"question": question, "answers": answers, "reward": reward})
    await set_questions(pool, questions)


async def delete_question(pool: asyncpg.Pool, index: int) -> None:
    questions = await get_questions(pool)

    if 0 <= index < len(questions):
        questions.pop(index)
        await set_questions(pool, questions)


async def get_trivia_timeout(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, TRIVIA_TIMEOUT_KEY, DEFAULT_TRIVIA_TIMEOUT)


async def set_trivia_timeout(pool: asyncpg.Pool, seconds: int) -> None:
    await set_setting(pool, TRIVIA_TIMEOUT_KEY, seconds)
