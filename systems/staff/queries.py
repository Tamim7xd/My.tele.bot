"""
نظام staff - استعلامات قاعدة البيانات.

يحتوي على دوال خاصة بلوحتي "مشرف" و"ادمن":
- عدد/قائمة المخالفين (أعضاء لهم سجل violation)
- تمديد الكتم
- تخفيض عدد التحذيرات (حذف آخر تحذير مسجَّل)
"""

from datetime import datetime, timedelta

import asyncpg


async def get_violators_count(pool: asyncpg.Pool) -> int:
    """يرجع عدد الأعضاء الذين لديهم سجل مخالفة (violation) واحد أو أكثر."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM archive WHERE action_type = 'violation'"
        )
        return result or 0


async def get_violators_list(pool: asyncpg.Pool, offset: int = 0, limit: int = 5) -> list[asyncpg.Record]:
    """
    يرجع قائمة الأعضاء المخالفين (لهم سجل violation)، مرتبين تنازلياً
    حسب عدد المخالفات، مع بياناتهم الأساسية وعدد مخالفاتهم.
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                m.user_id,
                m.username,
                m.full_name,
                COUNT(a.id) AS violations_count
            FROM members m
            JOIN archive a ON a.user_id = m.user_id AND a.action_type = 'violation'
            GROUP BY m.user_id, m.username, m.full_name
            ORDER BY violations_count DESC
            OFFSET $1 LIMIT $2
            """,
            offset, limit,
        )


async def extend_mute(pool: asyncpg.Pool, user_id: int, extra_seconds: int) -> datetime | None:
    """
    يمدد مدة كتم عضو بعدد ثوانٍ إضافية.
    إذا لم يكن مكتوماً، يبدأ من الآن.
    يرجع تاريخ/وقت الانتهاء الجديد.
    """
    async with pool.acquire() as conn:
        current = await conn.fetchrow(
            "SELECT is_muted, muted_until FROM members WHERE user_id = $1",
            user_id,
        )

        if current is None:
            return None

        base_time = datetime.utcnow()

        if current["is_muted"] and current["muted_until"] and current["muted_until"] > base_time:
            base_time = current["muted_until"]

        new_until = base_time + timedelta(seconds=extra_seconds)

        await conn.execute(
            "UPDATE members SET is_muted = TRUE, muted_until = $1 WHERE user_id = $2",
            new_until, user_id,
        )

        return new_until


async def reduce_warning(pool: asyncpg.Pool, user_id: int) -> bool:
    """
    يخفض عدد تحذيرات عضو بواحد (يحذف آخر سجل 'warn' في الأرشيف).
    يرجع True لو تم الحذف، False لو لا يوجد تحذيرات للحذف.
    """
    async with pool.acquire() as conn:
        deleted_id = await conn.fetchval(
            """
            DELETE FROM archive
            WHERE id = (
                SELECT id FROM archive
                WHERE user_id = $1 AND action_type = 'warn'
                ORDER BY created_at DESC
                LIMIT 1
            )
            RETURNING id
            """,
            user_id,
        )

        return deleted_id is not None
