"""
صندوق الحظ (lucky_box) - الإعدادات.

outcomes: قائمة نتائج محتملة بالشكل:
[{"amount": 100, "weight": 60}, {"amount": 150, "weight": 25}, ...]
weight = الوزن النسبي (احتمالية الظهور)، كلما زاد الرقم زادت الفرصة.
المبلغ هو ما يربحه اللاعب (قد يكون أقل من رسوم الدخول = خسارة جزئية،
أو أكبر = ربح، أو 0 = خسارة كاملة).
"""

import random

import asyncpg

from core.database import get_setting, set_setting


LUCKY_BOX_ENTRY_FEE_KEY = "lucky_box_entry_fee"
DEFAULT_ENTRY_FEE = 100

LUCKY_BOX_OUTCOMES_KEY = "lucky_box_outcomes"

DEFAULT_OUTCOMES = [
    {"amount": 100, "weight": 60},
    {"amount": 150, "weight": 25},
    {"amount": 200, "weight": 10},
    {"amount": 0, "weight": 5},
]


async def get_entry_fee(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, LUCKY_BOX_ENTRY_FEE_KEY, DEFAULT_ENTRY_FEE)


async def set_entry_fee(pool: asyncpg.Pool, amount: int) -> None:
    await set_setting(pool, LUCKY_BOX_ENTRY_FEE_KEY, amount)


async def get_outcomes(pool: asyncpg.Pool) -> list[dict]:
    return await get_setting(pool, LUCKY_BOX_OUTCOMES_KEY, DEFAULT_OUTCOMES)


async def set_outcomes(pool: asyncpg.Pool, outcomes: list[dict]) -> None:
    await set_setting(pool, LUCKY_BOX_OUTCOMES_KEY, outcomes)


def pick_outcome(outcomes: list[dict]) -> dict:
    """يختار نتيجة عشوائية موزونة من قائمة النتائج."""
    weights = [o["weight"] for o in outcomes]
    return random.choices(outcomes, weights=weights, k=1)[0]
