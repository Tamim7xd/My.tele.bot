"""
نظام المتجر (shop) - استعلامات حالة العضو (عضويته، ألقابه، سجل المشتريات).
"""

import json
from datetime import datetime, timedelta

import asyncpg


async def get_member_membership_status(pool: asyncpg.Pool, user_id: int) -> dict | None:
    """
    يرجع {"membership_id": str, "expires_at": datetime} لعضو معين،
    أو None إن لم تكن له عضوية فعّالة (منتهية أو غير موجودة).
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT membership_id, membership_expires_at FROM members WHERE user_id = $1",
            user_id,
        )

    if row is None or row["membership_id"] is None:
        return None

    expires_at = row["membership_expires_at"]

    if expires_at is not None and expires_at < datetime.utcnow():
        return None

    return {"membership_id": row["membership_id"], "expires_at": expires_at}


async def set_member_membership(pool: asyncpg.Pool, user_id: int, membership_id: str, duration_seconds: int) -> datetime:
    """
    يفعّل عضوية لعضو، يرجع تاريخ الانتهاء الجديد.
    duration_seconds: المدة بالثواني (وحدة موحدة تدعم دقائق/ساعات/أيام/أشهر).
    duration_seconds=0 يعني بلا انتهاء (عضوية دائمة).
    """
    if duration_seconds <= 0:
        expires_at = None
    else:
        expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET membership_id = $1, membership_expires_at = $2 WHERE user_id = $3",
            membership_id, expires_at, user_id,
        )

    return expires_at


async def get_owned_titles(pool: asyncpg.Pool, user_id: int) -> list[str]:
    async with pool.acquire() as conn:
        raw = await conn.fetchval("SELECT owned_titles FROM members WHERE user_id = $1", user_id)

    if raw is None:
        return []

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []

    if isinstance(raw, list):
        return raw

    return []


async def add_owned_title(pool: asyncpg.Pool, user_id: int, title_id: str) -> None:
    owned = await get_owned_titles(pool, user_id)

    if title_id not in owned:
        owned.append(title_id)

        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE members SET owned_titles = $1::jsonb WHERE user_id = $2",
                json.dumps(owned), user_id,
            )


async def get_active_title(pool: asyncpg.Pool, user_id: int) -> str | None:
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT active_title FROM members WHERE user_id = $1", user_id)


async def set_active_title(pool: asyncpg.Pool, user_id: int, title_id: str | None) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET active_title = $1 WHERE user_id = $2",
            title_id, user_id,
        )


# ===== سجل المشتريات (للأرشيف) =====

async def log_purchase(pool: asyncpg.Pool, user_id: int, item_type: str, item_id: str, price: int) -> None:
    """item_type: 'membership' أو 'title'."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO shop_purchases (user_id, item_type, item_id, price) VALUES ($1, $2, $3, $4)",
            user_id, item_type, item_id, price,
        )


async def get_membership_owners(pool: asyncpg.Pool, membership_id: str, offset: int = 0, limit: int = 5) -> list[asyncpg.Record]:
    """يرجع كل من اشترى عضوية معينة (تاريخياً، حتى لو انتهت)."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT DISTINCT ON (sp.user_id) sp.user_id, m.username, m.full_name, sp.created_at
            FROM shop_purchases sp
            JOIN members m ON m.user_id = sp.user_id
            WHERE sp.item_type = 'membership' AND sp.item_id = $1
            ORDER BY sp.user_id, sp.created_at DESC
            OFFSET $2 LIMIT $3
            """,
            membership_id, offset, limit,
        )


async def get_membership_owners_count(pool: asyncpg.Pool, membership_id: str) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM shop_purchases WHERE item_type = 'membership' AND item_id = $1",
            membership_id,
        )
        return result or 0


# ===== سجل "مسح محادثتي" =====

async def log_clear_chat(pool: asyncpg.Pool, user_id: int, deleted_count: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO shop_clear_log (user_id, deleted_count) VALUES ($1, $2)",
            user_id, deleted_count,
        )


async def get_clear_chat_history_count(pool: asyncpg.Pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM shop_clear_log WHERE user_id = $1", user_id
        )
        return result or 0


async def get_clear_chat_history(pool: asyncpg.Pool, user_id: int, offset: int = 0, limit: int = 5) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT id, deleted_count, created_at
            FROM shop_clear_log
            WHERE user_id = $1
            ORDER BY created_at DESC
            OFFSET $2 LIMIT $3
            """,
            user_id, offset, limit,
        )


async def get_members_with_clear_history(pool: asyncpg.Pool, offset: int = 0, limit: int = 6) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT m.user_id, m.username, m.full_name, COUNT(s.id) AS clear_count
            FROM members m
            JOIN shop_clear_log s ON s.user_id = m.user_id
            GROUP BY m.user_id, m.username, m.full_name
            ORDER BY clear_count DESC
            OFFSET $1 LIMIT $2
            """,
            offset, limit,
        )


async def get_members_with_clear_history_count(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM shop_clear_log"
        )
        return result or 0


# ===== المكافأة اليومية للعضوية =====

async def get_last_membership_reward_at(pool: asyncpg.Pool, user_id: int) -> datetime | None:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT last_membership_reward_at FROM members WHERE user_id = $1", user_id
        )


async def set_last_membership_reward_at(pool: asyncpg.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET last_membership_reward_at = NOW() WHERE user_id = $1",
            user_id,
        )


async def get_all_active_memberships(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """يرجع كل الأعضاء الذين لديهم عضوية فعّالة حالياً (لم تنتهِ)."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, membership_id, membership_expires_at, last_membership_reward_at
            FROM members
            WHERE membership_id IS NOT NULL
              AND (membership_expires_at IS NULL OR membership_expires_at > NOW())
            """
        )


async def get_last_clear_chat_at(pool: asyncpg.Pool, user_id: int) -> datetime | None:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT last_clear_chat_at FROM members WHERE user_id = $1", user_id
        )


async def set_last_clear_chat_at(pool: asyncpg.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET last_clear_chat_at = NOW() WHERE user_id = $1",
            user_id,
        )


async def revoke_membership(pool: asyncpg.Pool, user_id: int) -> None:
    """يسحب/يعطّل عضوية عضو فوراً (يصبح بلا عضوية فعّالة)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET membership_id = NULL, membership_expires_at = NULL WHERE user_id = $1",
            user_id,
        )


async def extend_membership(pool: asyncpg.Pool, user_id: int, extra_seconds: int) -> datetime | None:
    """
    يمدد مدة عضوية عضو بعدد ثوانٍ إضافية (أو يقلصها إن كان extra_seconds سالباً).
    إذا لم تكن له عضوية فعّالة، لا يفعل شيئاً ويرجع None.
    يرجع تاريخ الانتهاء الجديد (أو None لو أصبحت بلا انتهاء/غير صالحة).
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT membership_id, membership_expires_at FROM members WHERE user_id = $1",
            user_id,
        )

    if row is None or row["membership_id"] is None:
        return None

    current_expires = row["membership_expires_at"]

    if current_expires is None:
        # عضوية دائمة - التمديد لا معنى له، نتجاهل
        return None

    base_time = current_expires if current_expires > datetime.utcnow() else datetime.utcnow()
    new_expires = base_time + timedelta(seconds=extra_seconds)

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET membership_expires_at = $1 WHERE user_id = $2",
            new_expires, user_id,
        )

    return new_expires


async def get_member_full_membership_info(pool: asyncpg.Pool, user_id: int) -> dict | None:
    """
    يرجع معلومات العضوية الخام للعضو (بدون فحص الانتهاء)، مفيدة لعرضها
    في صفحة العضو باللوحة حتى لو كانت منتهية (للسحب/التمديد/إعادة التفعيل).
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT membership_id, membership_expires_at FROM members WHERE user_id = $1",
            user_id,
        )

    if row is None or row["membership_id"] is None:
        return None

    is_active = row["membership_expires_at"] is None or row["membership_expires_at"] > datetime.utcnow()

    return {
        "membership_id": row["membership_id"],
        "expires_at": row["membership_expires_at"],
        "is_active": is_active,
    }
