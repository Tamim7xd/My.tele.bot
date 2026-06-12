"""
نقطة بداية تشغيل البوت.
هنا يتم إنشاء نسخة البوت، الاتصال بقاعدة البيانات،
وتسجيل جميع الأنظمة (routers) كل واحد بشكل مستقل.

عند إضافة نظام جديد، فقط:
1. أضف import له هنا
2. أضف dp.include_router(اسم_النظام.router)
بدون أي تأثير على الأنظمة الأخرى.
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
    # سيتم إضافة كل نظام هنا لاحقاً، كل نظام بسطر واحد مستقل
# ===== تسجيل الأنظمة (Routers) =====
    from systems.members import members as members_system
    dp.include_router(members_system.router)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
