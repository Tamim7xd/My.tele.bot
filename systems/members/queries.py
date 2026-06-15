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


async def add_or_update_member(pool: asyncpg.Pool, user_id: int, username: str | None, full_name: str) -> bool:
    """
    إضافة أو تحديث عضو في قاعدة البيانات
    ترجع True إذا تمت العملية بنجاح، False إذا فشلت
    """
    try:
        async with pool.acquire() as conn:
            # استخدام COALESCE للتعامل مع القيم الفارغة
            await conn.execute(
                """
                INSERT INTO members (user_id, username, full_name, balance, level, messages_count, rank, created_at)
                VALUES ($1, COALESCE($2, ''), COALESCE($3, 'مستخدم'), 0, 1, 0, 'member', NOW())
                ON CONFLICT (user_id) DO UPDATE 
                SET username = COALESCE(EXCLUDED.username, members.username),
                    full_name = COALESCE(EXCLUDED.full_name, members.full_name)
                """,
                user_id, username or '', full_name or 'مستخدم'
            )
        return True
    except Exception as e:
        print(f"خطأ في add_or_update_member: {e}")
        return False


async def force_add_member(pool: asyncpg.Pool, user_id: int, username: str = None, full_name: str = None) -> bool:
    """
    إضافة عضو بالقوة مع قيم افتراضية
    """
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO members (user_id, username, full_name, balance, level, messages_count, rank, created_at)
                VALUES ($1, $2, $3, 0, 1, 0, 'member', NOW())
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id, username or f"user_{user_id}", full_name or f"عضو {user_id}"
            )
        return True
    except Exception as e:
        print(f"خطأ في force_add_member: {e}")
        return False


async def ensure_member_exists(pool: asyncpg.Pool, user_id: int, bot=None, chat_id=None) -> bool:
    """
    التأكد من وجود العضو في قاعدة البيانات، وإضافته إذا لم يكن موجوداً
    """
    # أولاً: التحقق من وجود العضو
    member = await get_member(pool, user_id)
    
    if member is not None:
        return True
    
    # ثانياً: محاولة جلب معلومات العضو من التيليجرام
    username = None
    full_name = None
    
    if bot and chat_id:
        try:
            chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            user = chat_member.user
            username = user.username
            full_name = user.full_name
        except Exception as e:
            print(f"فشل جلب معلومات العضو {user_id}: {e}")
    
    # ثالثاً: إضافة العضو
    return await add_or_update_member(pool, user_id, username, full_name)


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