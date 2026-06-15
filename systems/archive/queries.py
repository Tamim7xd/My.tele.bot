"""
نظام الأرشيف - استعلامات قاعدة البيانات.

يعتمد على جدول archive المشترك (في core/database.py):
    id, user_id, action_type, amount, reason, replied_message, done_by, created_at

action_type المستخدمة في الأنظمة الأخرى:
    'deduct', 'reward', 'violation', 'mute', 'ban', 'warn'
"""

import asyncpg


CATEGORY_TYPES = {
    "violation": "violation",
    "deduct": "deduct",
    "reward": "reward",
    "mute": "mute",
    "ban": "ban",
    "warn": "warn",
}


async def get_category_count(pool: asyncpg.Pool, user_id: int, action_type: str) -> int:
    """يرجع عدد سجلات فئة معينة لعضو."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM archive WHERE user_id = $1 AND action_type = $2",
            user_id, action_type,
        )
        return result or 0


async def get_all_counts(pool: asyncpg.Pool, user_id: int) -> dict[str, int]:
    """يرجع عدد سجلات كل الفئات لعضو دفعة واحدة."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT action_type, COUNT(*) AS cnt
            FROM archive
            WHERE user_id = $1
            GROUP BY action_type
            """,
            user_id,
        )

    counts = {action_type: 0 for action_type in CATEGORY_TYPES}

    for row in rows:
        if row["action_type"] in counts:
            counts[row["action_type"]] = row["cnt"]

    return counts


async def get_category_entries(
    pool: asyncpg.Pool,
    user_id: int,
    action_type: str,
    offset: int = 0,
    limit: int = 10,
) -> list[asyncpg.Record]:
    """
    يرجع سجلات فئة معينة لعضو، مع اسم/يوزر من قام بالإجراء (done_by_name/done_by_username)،
    مرتبة من الأحدث للأقدم.
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                a.id,
                a.amount,
                a.reason,
                a.replied_message,
                a.done_by,
                a.created_at,
                d.full_name AS done_by_name,
                d.username AS done_by_username
            FROM archive a
            LEFT JOIN members d ON d.user_id = a.done_by
            WHERE a.user_id = $1 AND a.action_type = $2
            ORDER BY a.created_at DESC
            OFFSET $3 LIMIT $4
            """,
            user_id, action_type, offset, limit,
        )


async def get_all_entries(pool: asyncpg.Pool, user_id: int, limit_per_category: int = 10) -> dict[str, list[asyncpg.Record]]:
    """يرجع آخر سجلات كل الفئات لعضو (للملخص الكامل القابل للنسخ)."""
    result = {}

    for action_type in CATEGORY_TYPES:
        result[action_type] = await get_category_entries(pool, user_id, action_type, offset=0, limit=limit_per_category)

    return result
