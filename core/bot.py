"""
نقطة بداية تشغيل البوت.
هنا يتم إنشاء نسخة البوت، الاتصال بقاعدة البيانات،
وتسجيل جميع الأنظمة (routers) كل واحد بشكل مستقل.

عند إضافة نظام جديد، فقط:
1. أضف import له هنا
2. أضف dp.include_router(اسم_النظام.router)
بدون أي تأثير على الأنظمة الأخرى.

⚠️ ملاحظة مهمة عن الترتيب:
أي Router له شرط نص محدد (أمر معين مثل "ترتيب" أو "حساب" أو "خصم")
يجب أن يُسجَّل قبل members_system.router، لأن الأخير
يطابق كل رسائل المجموعة بدون شرط نص ويوقف المعالجة.
لذلك: أوامر الأنظمة الأخرى أولاً، ثم members في الأخير.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import BOT_TOKEN, validate_config
from core.database import connect_db, close_db


async def main() -> None:
    # التحقق من المتغيرات الأساسية قبل أي شيء
    validate_config()

    # إعداد تسجيل الأخطاء (Logging)
    logging.basicConfig(level=logging.INFO)

    # الاتصال بقاعدة البيانات وإنشاء الجداول
    await connect_db()

    # إنشاء نسخة البوت
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # إنشاء الـ Dispatcher (موزع التحديثات)
    dp = Dispatcher()

    # ===== تسجيل الأنظمة (Routers) =====
    # أولاً: الأنظمة ذات الأوامر المحددة (شرط نص) أو الفلاتر العامة

    from systems.owner import owner as owner_system
    dp.include_router(owner_system.router)

    from systems.moderators import moderators as moderators_system
    dp.include_router(moderators_system.router)

    from systems.wallet import leaderboard as wallet_leaderboard
    dp.include_router(wallet_leaderboard.router)

    from systems.rewards import rewards as rewards_system
    dp.include_router(rewards_system.router)

    from systems.cleanup import cleanup as cleanup_system
    dp.include_router(cleanup_system.router)

    # أخيراً: members (يطابق كل الرسائل - يجب أن يكون آخر شيء)
    from systems.members import members as members_system
    dp.include_router(members_system.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())