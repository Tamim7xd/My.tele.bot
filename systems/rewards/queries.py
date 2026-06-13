"""
نظام الخصم والمكافأة - استعلامات قاعدة البيانات.

يحتوي على دالة لتسجيل عملية الخصم/المكافأة/المخالفة في جدول archive
المشترك (المُنشأ في core/database.py).
"""

import asyncpg


async def log_archive_entry(
    pool: asyncpg.Pool,
    user_id: int,
    action_type: str,
    amount: int | None,
    reason: str | None,
    replied_message: str | None,
    done_by: int,
) -> None:
    """
    يسجل عملية في الأرشيف.

    action_type: 'deduct' / 'reward' / 'violation' / ... إلخ
    """
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO archive (user_id, action_type, amount, reason, replied_message, done_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id, action_type, amount, reason, replied_message, done_by,
        )
