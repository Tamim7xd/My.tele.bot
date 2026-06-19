"""
نظام المتجر (shop) - مجدول المكافأة اليومية.

يفحص دورياً (كل ساعة) كل الأعضاء ذوي عضوية فعّالة، ويعطي كل من
لم يحصل على مكافأته اليومية منذ 24 ساعة المكافأة المحددة لعضويته.
"""

import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from core.database import get_pool
from systems.shop import queries as shop_queries
from systems.shop import member_queries as shop_member_queries
from systems.wallet import wallet


CHECK_INTERVAL_SECONDS = 3600


async def _give_daily_rewards(bot: Bot) -> None:
    pool = await get_pool()

    active_memberships = await shop_member_queries.get_all_active_memberships(pool)

    for row in active_memberships:
        user_id = row["user_id"]
        membership_id = row["membership_id"]
        last_reward_at = row["last_membership_reward_at"]

        if last_reward_at is not None and datetime.utcnow() < last_reward_at + timedelta(hours=24):
            continue

        membership = await shop_queries.get_membership_by_id(pool, membership_id)

        if membership is None:
            continue

        daily_reward = membership.get("daily_reward", 0)

        if daily_reward <= 0:
            continue

        await wallet.add_balance(pool, user_id, daily_reward)
        await shop_member_queries.set_last_membership_reward_at(pool, user_id)

        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🎁 حصلت على مكافأتك اليومية من عضوية {membership['name']}: {daily_reward:,} د.ع",
            )
        except Exception:
            pass


async def shop_rewards_scheduler_loop(bot: Bot) -> None:
    """حلقة لا نهائية تفحص المكافآت اليومية كل ساعة."""
    while True:
        try:
            await _give_daily_rewards(bot)
        except Exception:
            pass

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
