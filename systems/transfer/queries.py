"""
نظام التحويل (transfer) - استعلامات/تخزين.
"""

import asyncpg

from core.database import get_setting, set_setting


MIN_TRANSFER_KEY = "transfer_min_amount"
MAX_TRANSFER_KEY = "transfer_max_amount"
FEE_PERCENT_KEY = "transfer_fee_percent"

DEFAULT_MIN_TRANSFER = 100
DEFAULT_MAX_TRANSFER = 0
DEFAULT_FEE_PERCENT = 0


async def get_min_transfer(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, MIN_TRANSFER_KEY, DEFAULT_MIN_TRANSFER)


async def set_min_transfer(pool: asyncpg.Pool, amount: int) -> None:
    await set_setting(pool, MIN_TRANSFER_KEY, amount)


async def get_max_transfer(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, MAX_TRANSFER_KEY, DEFAULT_MAX_TRANSFER)


async def set_max_transfer(pool: asyncpg.Pool, amount: int) -> None:
    await set_setting(pool, MAX_TRANSFER_KEY, amount)


async def get_fee_percent(pool: asyncpg.Pool) -> int:
    return await get_setting(pool, FEE_PERCENT_KEY, DEFAULT_FEE_PERCENT)


async def set_fee_percent(pool: asyncpg.Pool, percent: int) -> None:
    await set_setting(pool, FEE_PERCENT_KEY, percent)


def parse_transfer_amount(text: str) -> int | None:
    """
    يحوّل نص المبلغ لرقم صحيح موجب، يدعم كل الصيغ:
    - 1000
    - 1.000 (نقطة كفاصل آلاف)
    - 1,000 (فاصلة لاتينية)
    - 1،000 (فاصلة عربية U+060C)
    """
    if not text:
        return None

    cleaned = (text.strip()
               .replace(".", "")
               .replace(",", "")
               .replace("\u060C", "")
               .replace(" ", ""))

    if not cleaned.isdigit():
        return None

    value = int(cleaned)
    return value if value > 0 else None
