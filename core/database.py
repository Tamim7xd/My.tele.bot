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
                protection_exceptions JSONB DEFAULT '{}',
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                last_game_at TIMESTAMP,
                membership_id TEXT,
                membership_expires_at TIMESTAMP,
                active_title TEXT,
                owned_titles JSONB DEFAULT '[]',
                last_membership_reward_at TIMESTAMP,
                last_clear_chat_at TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE,
                is_muted BOOLEAN DEFAULT FALSE,
                muted_until TIMESTAMP,
                banned_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # ===== ترقية الجداول القديمة (إضافة أعمدة جديدة إن لم تكن موجودة) =====
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS protection_exceptions JSONB DEFAULT '{}'"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS games_played INTEGER DEFAULT 0"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS membership_id TEXT"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS membership_expires_at TIMESTAMP"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS active_title TEXT"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS owned_titles JSONB DEFAULT '[]'"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS last_membership_reward_at TIMESTAMP"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS last_clear_chat_at TIMESTAMP"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS games_won INTEGER DEFAULT 0"
        )
        await conn.execute(
            "ALTER TABLE members ADD COLUMN IF NOT EXISTS last_game_at TIMESTAMP"
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

        # ===== جدول سجل المحذوفات (نظام protection) =====
        # منعزل تماماً عن archive - يخزن كل رسالة حذفها نظام الحماية
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS protection_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                violation_type TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # ===== جدول سجل مشتريات المتجر (عضويات وألقاب) =====
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_purchases (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                item_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                price BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # ===== جدول سجل "مسح محادثتي" (عدد الرسائل المحذوفة لكل استخدام) =====
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_clear_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES members(user_id),
                deleted_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # ===== جدول الإعدادات (key-value مشترك بين كل الأنظمة) =====
        # تُستخدم لتخزين القيم القابلة للتعديل من لوحة التحكم
        # (مثل قيم الخصم/المكافأة، عدد رسائل التنظيف، إلخ)
        # بدون الحاجة لتعديل الكود أو إعادة النشر.
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL
            );
            """
        )


async def get_setting(pool: asyncpg.Pool, key: str, default=None):
    """
    يرجع قيمة إعداد معين من جدول settings.
    إذا لم يكن موجوداً، يرجع default المُمرر.

    القيمة تُخزَّن وتُسترجع كـ JSON، لذا يمكن أن تكون
    عدداً، نصاً، قائمة، أو dict.
    """
    import json

    async with pool.acquire() as conn:
        raw = await conn.fetchval("SELECT value FROM settings WHERE key = $1", key)

    if raw is None:
        return default

    if isinstance(raw, str):
        return json.loads(raw)

    return raw


async def set_setting(pool: asyncpg.Pool, key: str, value) -> None:
    """
    يحدد/يحدّث قيمة إعداد معين في جدول settings.
    value يمكن أن يكون عدداً، نصاً، قائمة، أو dict (يُخزَّن كـ JSON).
    """
    import json

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2::jsonb)
            ON CONFLICT (key) DO UPDATE SET value = $2::jsonb
            """,
            key, json.dumps(value),
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
