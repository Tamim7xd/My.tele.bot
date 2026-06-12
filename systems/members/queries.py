"""
استعلامات قاعدة البيانات الخاصة بنظام الأعضاء.
يستخدم جدول members المُنشأ في core/database.py
ويستخدم جدول archive لعرض عدد المخالفات والتحذيرات.
"""

import asyncpg


async def ensure_member_exists(
    pool: asyncpg.Pool,
    user_id: int,
    username: str | None,
    full_name: str,
) -> None:
    """
    يضيف العضو لجدول members إذا لم يكن موجوداً.
    إذا كان موجوداً، يحدّث اسمه ويوزره (قد يتغيران بمرور الوقت).
    """
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO members (user_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET username = $2, full_name = $3
            """,
            user_id, username, full_name,
        )


async def increment_message_count(pool: asyncpg.Pool, user_id: int) -> None:
    """يزيد عداد رسائل العضو بواحد."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET messages_count = messages_count + 1 WHERE user_id = $1",
            user_id,
        )


async def get_member(pool: asyncpg.Pool, user_id: int) -> asyncpg.Record | None:
    """يرجع بيانات عضو واحد من جدول members."""
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM members WHERE user_id = $1",
            user_id,
        )


async def get_warnings_count(pool: asyncpg.Pool, user_id: int) -> int:
    """يرجع عدد التحذيرات المسجلة للعضو في الأرشيف."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM archive WHERE user_id = $1 AND action_type = 'warn'",
            user_id,
        )
        return result or 0


async def get_violations_count(pool: asyncpg.Pool, user_id: int) -> int:
    """
    يرجع عدد المخالفات المسجلة للعضو في الأرشيف.
    المخالفة = أي إجراء (خصم/كتم/حظر) تم تعليمه كمخالفة.
    """
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM archive WHERE user_id = $1 AND action_type = 'violation'",
            user_id,
        )
        return result or 0


async def get_rank(pool: asyncpg.Pool, user_id: int) -> str:
    """يرجع رتبة العضو (member / moderator / admin / owner)."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1",
            user_id,
        )
        return result or "member"


async def get_all_members(pool: asyncpg.Pool, offset: int = 0, limit: int = 6) -> list[asyncpg.Record]:
    """
    يرجع قائمة الأعضاء بشكل مقسّم (للأزرار، 6 في كل صفحة افتراضياً).
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT user_id, username, full_name FROM members ORDER BY created_at ASC OFFSET $1 LIMIT $2",
            offset, limit,
        )


async def get_members_count(pool: asyncpg.Pool) -> int:
    """يرجع العدد الإجمالي للأعضاء المسجلين."""
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM members")
        return result or 0


async def search_member(pool: asyncpg.Pool, query: str) -> list[asyncpg.Record]:
    """
    يبحث عن عضو بالاسم أو اليوزر (بحث جزئي غير حساس لحالة الأحرف).
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, full_name FROM members
            WHERE full_name ILIKE '%' || $1 || '%'
               OR username ILIKE '%' || $1 || '%'
            LIMIT 10
            """,
            query,
        )
