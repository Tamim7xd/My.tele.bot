"""
نظام الرصيد - الدوال المشتركة.

هذا الملف لا يحتوي على أي Router أو معالجة رسائل مباشرة،
بل دوال مساعدة (helpers) تستخدمها أنظمة أخرى (rewards, shop,
transfer, games, levels, daily_gift...) لتعديل رصيد الأعضاء
بطريقة موحدة وآمنة، دون أن يكرر كل نظام كود SQL الخاص به.

أي نظام يريد إضافة/خصم رصيد يستورد هذا الملف فقط:

    from systems.wallet import wallet

    await wallet.add_balance(pool, user_id, 1000)
    await wallet.deduct_balance(pool, user_id, 500)
"""

import asyncpg


async def get_balance(pool: asyncpg.Pool, user_id: int) -> int:
    """يرجع الرصيد الحالي لعضو معين."""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT balance FROM members WHERE user_id = $1",
            user_id,
        )
        return result or 0


async def add_balance(pool: asyncpg.Pool, user_id: int, amount: int) -> int:
    """
    يضيف مبلغاً لرصيد العضو ويرجع الرصيد الجديد.
    amount يجب أن يكون قيمة موجبة.
    """
    async with pool.acquire() as conn:
        new_balance = await conn.fetchval(
            "UPDATE members SET balance = balance + $1 WHERE user_id = $2 RETURNING balance",
            amount, user_id,
        )
        return new_balance or 0


async def deduct_balance(pool: asyncpg.Pool, user_id: int, amount: int) -> bool:
    """
    يخصم مبلغاً من رصيد العضو.
    يرجع True لو نجح الخصم (الرصيد كان كافياً)،
    و False لو الرصيد غير كافٍ (لا يتم أي تعديل في هذه الحالة).
    """
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            UPDATE members
            SET balance = balance - $1
            WHERE user_id = $2 AND balance >= $1
            RETURNING balance
            """,
            amount, user_id,
        )
        return result is not None


async def set_balance(pool: asyncpg.Pool, user_id: int, amount: int) -> None:
    """يحدد رصيد العضو لقيمة معينة مباشرة (يُستخدم من لوحة التحكم)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE members SET balance = $1 WHERE user_id = $2",
            amount, user_id,
        )


async def transfer_balance(
    pool: asyncpg.Pool,
    from_user_id: int,
    to_user_id: int,
    amount: int,
) -> bool:
    """
    يحول مبلغاً من عضو لعضو آخر بشكل آمن (داخل معاملة واحدة - Transaction).
    يرجع True لو نجح التحويل، و False لو رصيد المُحوِّل غير كافٍ.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            deducted = await conn.fetchval(
                """
                UPDATE members
                SET balance = balance - $1
                WHERE user_id = $2 AND balance >= $1
                RETURNING balance
                """,
                amount, from_user_id,
            )

            if deducted is None:
                return False

            await conn.execute(
                "UPDATE members SET balance = balance + $1 WHERE user_id = $2",
                amount, to_user_id,
            )

            return True


async def get_top_balances(pool: asyncpg.Pool, limit: int = 10) -> list[asyncpg.Record]:
    """يرجع قائمة أعلى الأعضاء رصيداً (للترتيب - Leaderboard)."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, username, full_name, balance
            FROM members
            ORDER BY balance DESC
            LIMIT $1
            """,
            limit,
        )


async def get_total_balance(pool: asyncpg.Pool) -> int:
    """يرجع إجمالي الرصيد المتداول بين جميع الأعضاء."""
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COALESCE(SUM(balance), 0) FROM members")
        return result or 0
