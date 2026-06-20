"""
نظام المتجر (shop) - مجدول المكافأة اليومية + تنبيه انتهاء العضوية.

يفحص دورياً (كل ساعة):
1. كل الأعضاء ذوي عضوية فعّالة، ويعطي كل من لم يحصل على مكافأته
   اليومية منذ 24 ساعة المكافأة المحددة لعضويته.
2. كل الأعضاء الذين تنتهي عضويتهم خلال 24 ساعة القادمة ولم يُنبَّهوا
   بعد، ويرسل لهم تنبيهاً في الخاص + في المجموعة.
"""

import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from core.database import get_pool, get_setting
from systems.shop import queries as shop_queries
from systems.shop import member_queries as shop_member_queries
from systems.wallet import wallet


CHECK_INTERVAL_SECONDS = 3600
EXPIRY_WARNING_HOURS = 24


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


async def _warn_expiring_memberships(bot: Bot) -> None:
    pool = await get_pool()

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    expiring = await shop_member_queries.get_members_expiring_soon(pool, within_hours=EXPIRY_WARNING_HOURS)

    for row in expiring:
        user_id = row["user_id"]
        full_name = row["full_name"]
        username = row["username"]
        membership_id = row["membership_id"]
        expires_at = row["membership_expires_at"]

        membership = await shop_queries.get_membership_by_id(pool, membership_id)
        membership_name = membership["name"] if membership else membership_id

        expires_str = expires_at.strftime("%Y-%m-%d %H:%M")

        private_text = (
            f"⏳ تنبيه: عضويتك {membership_name} ستنتهي خلال أقل من 24 ساعة "
            f"(بتاريخ {expires_str}). جدّدها من المتجر قبل انتهائها."
        )

        username_display = f"@{username}" if username else full_name

        group_text = (
            f"⏳ تنبيه: عضوية {full_name} ({username_display}) ستنتهي خلال أقل من 24 ساعة."
        )

        try:
            await bot.send_message(chat_id=user_id, text=private_text)
        except Exception:
            pass

        if group_id:
            try:
                await bot.send_message(chat_id=group_id, text=group_text)
            except Exception:
                pass

        await shop_member_queries.mark_expiry_warned(pool, user_id)


async def shop_rewards_scheduler_loop(bot: Bot) -> None:
    """حلقة لا نهائية تفحص المكافآت اليومية وتنبيهات انتهاء العضوية كل ساعة."""
    while True:
        try:
            await _give_daily_rewards(bot)
        except Exception:
            pass

        try:
            await _warn_expiring_memberships(bot)
        except Exception:
            pass

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
