"""
الناجي الأخير (last_survivor) - الإعدادات.
"""

import asyncpg

from core.database import get_setting, set_setting


ENTRY_FEE_KEY = "last_survivor_entry_fee"
DEFAULT_ENTRY_FEE = 500

JOIN_WINDOW_KEY = "last_survivor_join_window_seconds"
DEFAULT_JOIN_WINDOW = 30

MIN_PLAYERS_KEY = "last_survivor_min_players"
DEFAULT_MIN_PLAYERS = 2

ELIMINATION_DELAY_KEY = "last_survivor_elimination_delay_seconds"
DEFAULT_ELIMINATION_DELAY = 2


async def get_entry_fee(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, ENTRY_FEE_KEY, DEFAULT_ENTRY_FEE)


async def set_entry_fee(pool: asyncpg.Pool, amount: int) -> None:
    await set_setting(pool, ENTRY_FEE_KEY, amount)


async def get_join_window(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, JOIN_WINDOW_KEY, DEFAULT_JOIN_WINDOW)


async def set_join_window(pool: asyncpg.Pool, seconds: int) -> None:
    await set_setting(pool, JOIN_WINDOW_KEY, seconds)


async def get_min_players(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, MIN_PLAYERS_KEY, DEFAULT_MIN_PLAYERS)


async def set_min_players(pool: asyncpg.Pool, count: int) -> None:
    await set_setting(pool, MIN_PLAYERS_KEY, count)


async def get_elimination_delay(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, ELIMINATION_DELAY_KEY, DEFAULT_ELIMINATION_DELAY)


async def set_elimination_delay(pool: asyncpg.Pool, seconds: int) -> None:
    await set_setting(pool, ELIMINATION_DELAY_KEY, seconds)
