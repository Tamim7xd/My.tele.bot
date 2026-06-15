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
أو حالات FSM (مثل لوحة التحكم "admin")
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
from core.database import connect_db, close_db, get_setting


async def main() -> None:
    # التحقق من المتغيرات الأساسية قبل أي شيء
    validate_config()

    # إعداد تسجيل الأخطاء (Logging)
    logging.basicConfig(level=logging.INFO)

    # الاتصال بقاعدة البيانات وإنشاء الجداول
    pool = await connect_db()

    # إنشاء نسخة البوت
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # إنشاء الـ Dispatcher (موزع التحديثات)
    dp = Dispatcher()

    # ===== تسجيل الأنظمة (Routers) =====
    # أولاً: لوحة التحكم (admin) وكل لوحاتها الفرعية - تحتوي على FSM وحالات
    # يجب أن تُسجَّل قبل أي شيء يطابق كل الرسائل

    from systems.owner import owner as owner_system
    dp.include_router(owner_system.router)

    from systems.owner import members_panel
    dp.include_router(members_panel.router)

    from systems.owner import archive_panel
    dp.include_router(archive_panel.router)

    from systems.owner import moderators_panel
    dp.include_router(moderators_panel.router)

    from systems.owner import levels_panel
    dp.include_router(levels_panel.router)

    from systems.owner import moderation_panel
    dp.include_router(moderation_panel.router)

    from systems.owner import announcements_panel
    dp.include_router(announcements_panel.router)

    # ثانياً: الأنظمة ذات الأوامر المحددة (شرط نص) أو الفلاتر العامة

    from systems.moderators import moderators as moderators_system
    dp.include_router(moderators_system.router)

    from systems.wallet import leaderboard as wallet_leaderboard
    dp.include_router(wallet_leaderboard.router)

    from systems.rewards import rewards as rewards_system
    dp.include_router(rewards_system.router)

    from systems.moderation import moderation as moderation_system
    dp.include_router(moderation_system.router)

    from systems.staff import staff as staff_system
    dp.include_router(staff_system.router)

    from systems.cleanup import cleanup as cleanup_system
    dp.include_router(cleanup_system.router)

    from systems.announcements import announcements as announcements_system
    dp.include_router(announcements_system.router)

    # أخيراً: members (يطابق كل الرسائل - يجب أن يكون آخر شيء)
    from systems.members import members as members_system
    dp.include_router(members_system.router)

    # ===== المجدولات الخلفية (Background Tasks) =====
    # مجدول رفع الكتم/الحظر المنتهي - يعمل في الخلفية بشكل مستقل
    from systems.moderation.scheduler import moderation_scheduler_loop
    from systems.members.members import GROUP_ID_KEY

    group_id = await get_setting(pool, GROUP_ID_KEY)
    asyncio.create_task(moderation_scheduler_loop(bot, group_id))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
