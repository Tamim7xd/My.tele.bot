"""
نظام الإداريين - استعلامات قاعدة البيانات.

يحتوي على دوال لإدارة الرتب والصلاحيات المخصصة:
- ترقية / تخفيض عضو
- تفعيل / إزالة صلاحية مخصصة لعضو معين
- جلب قوائم الأدمن والمشرفين
"""

import json

import asyncpg

from systems.moderators.permissions import RANKS_ORDER


async def set_rank(pool: asyncpg.Pool, user_id: int, rank: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET rank = $1 WHERE user_id = $2",
            rank, user_id,
        )


async def promote(pool: asyncpg.Pool, user_id: int) -> str | None:
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1", user_id
        ) or "member"

    if current == "owner" or current == "admin":
        return None

    new_rank = RANKS_ORDER[RANKS_ORDER.index(current) + 1]

    if new_rank == "owner":
        return None

    await set_rank(pool, user_id, new_rank)
    return new_rank


async def demote(pool: asyncpg.Pool, user_id: int) -> str | None:
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT rank FROM members WHERE user_id = $1", user_id
        ) or "member"

    if current in ("member", "owner"):
        return None

    new_rank = RANKS_ORDER[RANKS_ORDER.index(current) - 1]

    await set_rank(pool, user_id, new_rank)
    return new_rank


async def get_staff_list(pool: asyncpg.Pool, rank: str, offset: int = 0, limit: int = 6) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, full_name FROM members
            WHERE rank = $1
            ORDER BY created_at ASC
            OFFSET $2 LIMIT $3
            """,
            rank, offset, limit,
        )


async def get_staff_count(pool: asyncpg.Pool, rank: str) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM members WHERE rank = $1", rank
        )
        return result or 0


async def add_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT permissions FROM members WHERE user_id = $1", user_id
        )
        custom_raw = (row["permissions"] if row else None) or "{}"
        custom = json.loads(custom_raw) if isinstance(custom_raw, str) else custom_raw

        added = set(custom.get("add", []))
        removed = set(custom.get("remove", []))

        added.add(permission)
        removed.discard(permission)

        custom["add"] = list(added)
        custom["remove"] = list(removed)

        await conn.execute(
            "UPDATE members SET permissions = $1::jsonb WHERE user_id = $2",
            json.dumps(custom), user_id,
        )


async def remove_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT permissions FROM members WHERE user_id = $1", user_id
        )
        custom_raw = (row["permissions"] if row else None) or "{}"
        custom = json.loads(custom_raw) if isinstance(custom_raw, str) else custom_raw

        added = set(custom.get("add", []))
        removed = set(custom.get("remove", []))

        removed.add(permission)
        added.discard(permission)

        custom["add"] = list(added)
        custom["remove"] = list(removed)

        await conn.execute(
            "UPDATE members SET permissions = $1::jsonb WHERE user_id = $2",
            json.dumps(custom), user_id,
        )
