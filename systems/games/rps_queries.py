"""
لعبة حجر ورقة مقص (rps) - إعدادات المكافأة.
"""

import asyncpg

from core.database import get_setting, set_setting


RPS_REWARD_KEY = "rps_reward"
DEFAULT_RPS_REWARD = 1000


async def get_rps_reward(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, RPS_REWARD_KEY, DEFAULT_RPS_REWARD)


async def set_rps_reward(pool: asyncpg.Pool, amount: int) -> None:
    await set_setting(pool, RPS_REWARD_KEY, amount)
