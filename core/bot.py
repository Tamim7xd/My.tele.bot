"""
نقطة بداية تشغيل البوت.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import BOT_TOKEN, validate_config
from core.database import connect_db, close_db, get_setting


async def main() -> None:
    validate_config()
    logging.basicConfig(level=logging.INFO)
    pool = await connect_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # ===== تسجيل الأنظمة (Routers) =====
    # أولاً: لوحة التحكم (admin) وكل لوحاتها الفرعية

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

    from systems.owner import protection_panel
    dp.include_router(protection_panel.router)

    # ⭐ نظام العضويات الإدارية الجديد
    from systems.owner import ranks_panel
    dp.include_router(ranks_panel.router)

    # ثانياً: الأنظمة ذات الأوامر المحددة

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

    from systems.protection import protection as protection_system
    dp.include_router(protection_system.router)

    from systems.announcements import announcements as announcements_system
    dp.include_router(announcements_system.router)

    # أخيراً: members (يطابق كل الرسائل)
    from systems.members import members as members_system
    dp.include_router(members_system.router)

    # ===== المجدولات الخلفية =====
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
