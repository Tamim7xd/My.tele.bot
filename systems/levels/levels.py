"""
نظام المستويات - الملف الرئيسي.

القاعدة المتفق عليها:
- المستوى 1: تلقائي عند الانضمام (كل عضو جديد)
- المستويات 2-5: كل مستوى يحتاج 50 رسالة إضافية
- المستوى 6+: كل مستوى يحتاج 100 رسالة إضافية
- عند رفع المستوى: + 1,000 د.ع مكافأة + إشعار للمجموعة

القيم (REQUIRED_MESSAGES_TIERS, LEVEL_UP_REWARD) قابلة للتعديل
من لوحة التحكم (محفوظة في جدول settings)، هذا الملف يقرأها
من هناك أو يستخدم القيم الافتراضية أول مرة.

check_level_up يُستدعى من systems/members/members.py بعد كل
زيادة في عداد الرسائل.
"""

from aiogram import Bot

from core.database import get_setting, set_setting
from systems.wallet import wallet
from systems.levels.notifications import messages


# ===== الإعدادات الافتراضية (قابلة للتعديل من لوحة التحكم) =====

# المستويات 2-5: كل مستوى يحتاج 50 رسالة إضافية عن المستوى السابق
# المستوى 6+: كل مستوى يحتاج 100 رسالة إضافية
LEVEL_UP_REWARD_KEY = "level_up_reward"
DEFAULT_LEVEL_UP_REWARD = 1_000

MESSAGES_TIER_1_5_KEY = "level_messages_1_5"  # المستويات 2-5
DEFAULT_MESSAGES_TIER_1_5 = 50

MESSAGES_TIER_6_PLUS_KEY = "level_messages_6_plus"  # المستوى 6+
DEFAULT_MESSAGES_TIER_6_PLUS = 100


async def get_level_up_reward(pool) -> int:
    return await get_setting(pool, LEVEL_UP_REWARD_KEY, DEFAULT_LEVEL_UP_REWARD)


async def get_messages_tier_1_5(pool) -> int:
    return await get_setting(pool, MESSAGES_TIER_1_5_KEY, DEFAULT_MESSAGES_TIER_1_5)


async def get_messages_tier_6_plus(pool) -> int:
    return await get_setting(pool, MESSAGES_TIER_6_PLUS_KEY, DEFAULT_MESSAGES_TIER_6_PLUS)


async def messages_required_for_level(pool, level: int) -> int:
    """
    يرجع إجمالي عدد الرسائل المطلوب (تراكمي) للوصول لمستوى معين.

    المستوى 1: 0 رسالة (تلقائي)
    المستوى 2: tier_1_5 رسالة
    المستوى 3: 2 * tier_1_5
    المستوى 4: 3 * tier_1_5
    المستوى 5: 4 * tier_1_5
    المستوى 6: 4 * tier_1_5 + tier_6_plus
    المستوى N (N>=6): 4 * tier_1_5 + (N - 5) * tier_6_plus
    """
    if level <= 1:
        return 0

    tier_1_5 = await get_messages_tier_1_5(pool)
    tier_6_plus = await get_messages_tier_6_plus(pool)

    if level <= 5:
        return (level - 1) * tier_1_5

    return 4 * tier_1_5 + (level - 5) * tier_6_plus


async def check_level_up(
    pool,
    bot: Bot,
    chat_id: int,
    user_id: int,
    username: str | None,
    full_name: str,
    messages_count: int,
) -> None:
    """
    يفحص إن كان عدد رسائل العضو الحالي كافياً لرفع مستوى واحد أو أكثر،
    ويطبق الرفع تلقائياً (مع المكافأة والإشعار) لكل مستوى يستحقه.

    يستدعى بعد كل زيادة في عداد الرسائل.
    """
    from systems.members import queries as members_queries

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        return

    current_level = member["level"]
    reward = await get_level_up_reward(pool)

    # قد يرتفع العضو أكثر من مستوى دفعة واحدة (مثلاً أرسل عدة رسائل بسرعة)
    while True:
        next_level = current_level + 1
        required = await messages_required_for_level(pool, next_level)

        if messages_count < required:
            break

        current_level = next_level

        await members_queries.set_level(pool, user_id, current_level)
        await wallet.add_balance(pool, user_id, reward)

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=messages.level_up_notification(full_name, username, current_level, reward),
            )
        except Exception:
            pass
