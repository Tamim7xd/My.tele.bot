"""
استعلامات قاعدة البيانات لنظام الأعضاء
"""

import json
from typing import Optional, List, Dict, Any

import asyncpg

from core.database import get_pool


async def get_member(pool: asyncpg.Pool, user_id: int) -> Optional[Dict[str, Any]]:
    """جلب بيانات عضو معين"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM members WHERE user_id = $1",
            user_id
        )
    
    if row is None:
        return None
    
    return dict(row)


async def get_all_members(pool: asyncpg.Pool, offset: int = 0, limit: int = 6) -> List[Dict[str, Any]]:
    """جلب جميع الأعضاء مع ترقيم الصفحات"""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, username, full_name, balance, level, rank, is_muted, is_banned
            FROM members
            ORDER BY user_id
            OFFSET $1 LIMIT $2
            """,
            offset, limit
        )
    
    return [dict(row) for row in rows]


async def get_members_count(pool: asyncpg.Pool) -> int:
    """عدد الأعضاء الكلي"""
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM members")
        return result or 0


async def add_or_update_member(pool: asyncpg.Pool, user_id: int, username: str | None, full_name: str) -> None:
    """إضافة أو تحديث عضو في قاعدة البيانات"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO members (user_id, username, full_name, balance, level, messages_count, rank, created_at)
            VALUES ($1, $2, $3, 0, 1, 0, 'member', NOW())
            ON CONFLICT (user_id) DO UPDATE 
            SET username = EXCLUDED.username, 
                full_name = EXCLUDED.full_name
            """,
            user_id, username, full_name
        )


async def update_member_balance(pool: asyncpg.Pool, user_id: int, new_balance: int) -> None:
    """تحديث رصيد العضو"""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET balance = $1 WHERE user_id = $2",
            new_balance, user_id
        )


async def update_member_level(pool: asyncpg.Pool, user_id: int, new_level: int) -> None:
    """تحديث مستوى العضو"""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET level = $1 WHERE user_id = $2",
            new_level, user_id
        )


async def update_member_rank(pool: asyncpg.Pool, user_id: int, new_rank: str) -> None:
    """تحديث رتبة العضو"""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET rank = $1 WHERE user_id = $2",
            new_rank, user_id
        )


async def increment_messages_count(pool: asyncpg.Pool, user_id: int) -> int:
    """زيادة عدد رسائل العضو وإرجاع العدد الجديد"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            UPDATE members 
            SET messages_count = messages_count + 1 
            WHERE user_id = $1 
            RETURNING messages_count
            """,
            user_id
        )
        return result or 1


async def search_members(pool: asyncpg.Pool, search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """البحث عن أعضاء بالاسم أو اليوزرنيم"""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, username, full_name
            FROM members
            WHERE full_name ILIKE $1 OR username ILIKE $1
            LIMIT $2
            """,
            f"%{search_text}%", limit
        )
    
    return [dict(row) for row in rows]


async def get_member_rank(pool: asyncpg.Pool, user_id: int) -> str:
    """جلب رتبة العضو"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id
        )
        return result or "member"


async def get_member_balance(pool: asyncpg.Pool, user_id: int) -> int:
    """جلب رصيد العضو"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT balance FROM members WHERE user_id = $1",
            user_id
        )
        return result or 0


async def get_member_level(pool: asyncpg.Pool, user_id: int) -> int:
    """جلب مستوى العضو"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT level FROM members WHERE user_id = $1",
            user_id
        )
        return result or 1


async def is_member_muted(pool: asyncpg.Pool, user_id: int) -> bool:
    """التحقق إذا كان العضو مكتوماً"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT is_muted FROM members WHERE user_id = $1",
            user_id
        )
        return result or False


async def is_member_banned(pool: asyncpg.Pool, user_id: int) -> bool:
    """التحقق إذا كان العضو محظوراً"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT is_banned FROM members WHERE user_id = $1",
            user_id
        )
        return result or False


async def get_muted_until(pool: asyncpg.Pool, user_id: int) -> Optional[str]:
    """جلب تاريخ انتهاء الكتم"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT muted_until FROM members WHERE user_id = $1",
            user_id
        )
        return result


async def get_banned_until(pool: asyncpg.Pool, user_id: int) -> Optional[str]:
    """جلب تاريخ انتهاء الحظر"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT banned_until FROM members WHERE user_id = $1",
            user_id
        )
        return result