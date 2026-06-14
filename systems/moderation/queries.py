"""
نظام الحظر/الكتم/التحذير - استعلامات قاعدة البيانات.
"""

from datetime import datetime, timedelta

import asyncpg


async def set_mute(pool: asyncpg.Pool, user_id: int, until: datetime | None) -> None:
    """
    يضع/يرفع الكتم عن عضو.
    until=None يعني كتم دائم. تمرير قيمة في الماضي أو is_muted=False يرفع الكتم.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET is_muted = TRUE, muted_until = $1 WHERE user_id = $2",
            until, user_id,
        )


async def unmute(pool: asyncpg.Pool, user_id: int) -> None:
    """يرفع الكتم عن عضو."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET is_muted = FALSE, muted_until = NULL WHERE user_id = $1",
            user_id,
        )


async def set_ban(pool: asyncpg.Pool, user_id: int, until: datetime | None) -> None:
    """
    يحظر عضو. until=None يعني حظر دائم.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET is_banned = TRUE, banned_until = $1 WHERE user_id = $2",
            until, user_id,
        )


async def unban(pool: asyncpg.Pool, user_id: int) -> None:
    """يرفع الحظر عن عضو."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET is_banned = FALSE, banned_until = NULL WHERE user_id = $1",
            user_id,
        )


async def get_moderation_status(pool: asyncpg.Pool, user_id: int) -> asyncpg.Record | None:
    """يرجع حالة الكتم/الحظر الحالية لعضو."""
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT is_muted, muted_until, is_banned, banned_until FROM members WHERE user_id = $1",
            user_id,
        )


async def get_expired_mutes(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """يرجع الأعضاء المكتومين الذين انتهت مدتهم (muted_until في الماضي)."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, full_name FROM members
            WHERE is_muted = TRUE AND muted_until IS NOT NULL AND muted_until <= NOW()
            """
        )


async def get_expired_bans(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """يرجع الأعضاء المحظورين الذين انتهت مدتهم (banned_until في الماضي)."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, full_name FROM members
            WHERE is_banned = TRUE AND banned_until IS NOT NULL AND banned_until <= NOW()
            """
        )


async def log_archive_entry(
    pool: asyncpg.Pool,
    user_id: int,
    action_type: str,
    reason: str | None,
    replied_message: str | None,
    done_by: int,
) -> None:
    """يسجل عملية في الأرشيف (نفس جدول archive المشترك)."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO archive (user_id, action_type, amount, reason, replied_message, done_by)
            VALUES ($1, $2, NULL, $3, $4, $5)
            """,
            user_id, action_type, reason, replied_message, done_by,
        )


def duration_to_datetime(seconds: int) -> datetime:
    """يحول عدد ثوانٍ إلى تاريخ/وقت مستقبلي (الآن + seconds)."""
    return datetime.utcnow() + timedelta(seconds=seconds)
