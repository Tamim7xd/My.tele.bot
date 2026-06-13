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
    """
    يحدد رتبة عضو مباشرة (member / moderator / admin / owner).
    يُستخدم في الترقية والتخفيض.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET rank = $1 WHERE user_id = $2",
            rank, user_id,
        )


async def promote(pool: asyncpg.Pool, user_id: int) -> str | None:
    """
    يرقي عضو لرتبة أعلى (member -> moderator -> admin).
    لا يمكن الترقية إلى owner عبر هذه الدالة.
    يرجع الرتبة الجديدة، أو None إذا كان العضو بأعلى رتبة ممكنة بالفعل.
    """
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
    """
    يخفض عضو لرتبة أدنى (admin -> moderator -> member).
    لا يمكن تخفيض owner عبر هذه الدالة.
    يرجع الرتبة الجديدة، أو None إذا كان العضو بالفعل "member" أو "owner".
    """
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
    """يرجع قائمة الأعضاء برتبة معينة (admin أو moderator) بشكل مقسّم."""
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
    """يرجع عدد الأعضاء برتبة معينة (admin أو moderator)."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM members WHERE rank = $1", rank
        )
        return result or 0


async def add_permission(pool: asyncpg.Pool, user_id: int, permission: str) -> None:
    """يضيف صلاحية مخصصة إضافية لعضو معين (خارج صلاحيات رتبته الافتراضية)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT permissions FROM members WHERE user_id = $1", user_id
        )
        custom = (row["permissions"] if row else None) or {}

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
    """يزيل صلاحية معينة عن عضو (حتى لو كانت من صلاحيات رتبته الافتراضية)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT permissions FROM members WHERE user_id = $1", user_id
        )
        custom = (row["permissions"] if row else None) or {}

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
