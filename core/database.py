"""
الاتصال بقاعدة بيانات PostgreSQL وإنشاء الجداول الأساسية.
كل نظام يمكنه إضافة جداوله الخاصة هنا أو في ملف منفصل لاحقاً،
دون التأثير على الجداول الأخرى.
"""

import asyncpg
from core.config import DATABASE_URL


# المتغير العام الذي يحمل اتصال (pool) قاعدة البيانات
db_pool: asyncpg.Pool | None = None


async def connect_db() -> asyncpg.Pool:
    """
    ينشئ اتصال (pool) بقاعدة البيانات ويخزنه في db_pool،
    ثم يقوم بإنشاء الجداول الأساسية إن لم تكن موجودة.
    """
    global db_pool

    db_pool = await asyncpg.create_pool(dsn=DATABASE_URL)

    await create_tables()

    return db_pool


async def create_tables() -> None:
    """
    ينشئ الجداول الأساسية المشتركة بين الأنظمة.
    كل جدول له IF NOT EXISTS لتجنب الأخطاء عند إعادة التشغيل.
    """
    assert db_pool is not None

    async with db_pool.acquire() as conn:

        # ===== جدول الأعضاء (الجدول المركزي المشترك) =====
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance BIGINT DEFAULT 0,
                level INTEGER DEFAULT 1,
                messages_count INTEGER DEFAULT 0,
                rank TEXT DEFAULT 'member',
                permissions JSONB DEFAULT '{}',
                is_banned BOOLEAN DEFAULT FALSE,
                is_muted BOOLEAN DEFAULT FALSE,
                muted_until TIMESTAMP,
                banned_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # ===== جدول الأرشيف (سجل الإجراءات لكل عضو) =====
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS archive (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                action_type TEXT NOT NULL,
                amount BIGINT,
                reason TEXT,
                replied_message TEXT,
                done_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )


async def get_pool() -> asyncpg.Pool:
    """
    يرجع اتصال قاعدة البيانات الحالي.
    تستخدمه جميع الأنظمة للوصول لقاعدة البيانات.
    """
    assert db_pool is not None, "قاعدة البيانات غير متصلة - تأكد من استدعاء connect_db أولاً"
    return db_pool


async def close_db() -> None:
    """يغلق الاتصال بقاعدة البيانات عند إيقاف البوت."""
    if db_pool is not None:
        await db_pool.close()
