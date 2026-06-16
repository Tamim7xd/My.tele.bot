"""
لعبة الألغاز (riddles) - استعلامات/تخزين.

نفس بنية trivia تماماً (سؤال + إجابات مقبولة متعددة + مكافأة)،
لكن بمحتوى ألغاز عراقية مضحكة وصعبة، ومخزَّنة بمفتاح مستقل.
"""

import asyncpg

from core.database import get_setting, set_setting


RIDDLES_KEY = "riddles_questions"
RIDDLES_TIMEOUT_KEY = "riddles_timeout_seconds"
DEFAULT_RIDDLES_TIMEOUT = 5


DEFAULT_RIDDLES = [
    {
        "question": "شي إذا قطعته زاد؟ 🤔",
        "answers": ["حبل", "الحبل"],
        "reward": 1500,
    },
    {
        "question": "بيت بلا أبواب ولا شبابيك، شنو هو؟",
        "answers": ["بيضة", "البيضة"],
        "reward": 1500,
    },
    {
        "question": "يدخل البيت بدون باب، شنو هو؟",
        "answers": ["ضوء", "النور", "الضوء", "نور"],
        "reward": 1500,
    },
]


async def get_riddles(pool: asyncpg.Pool) -> list[dict]:
    return await get_setting(pool, RIDDLES_KEY, DEFAULT_RIDDLES)


async def set_riddles(pool: asyncpg.Pool, riddles: list[dict]) -> None:
    await set_setting(pool, RIDDLES_KEY, riddles)


async def add_riddle(pool: asyncpg.Pool, question: str, answers: list[str], reward: int) -> None:
    riddles = await get_riddles(pool)
    riddles.append({"question": question, "answers": answers, "reward": reward})
    await set_riddles(pool, riddles)


async def delete_riddle(pool: asyncpg.Pool, index: int) -> None:
    riddles = await get_riddles(pool)

    if 0 <= index < len(riddles):
        riddles.pop(index)
        await set_riddles(pool, riddles)


async def get_riddles_timeout(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, RIDDLES_TIMEOUT_KEY, DEFAULT_RIDDLES_TIMEOUT)


async def set_riddles_timeout(pool: asyncpg.Pool, seconds: int) -> None:
    await set_setting(pool, RIDDLES_TIMEOUT_KEY, seconds)
