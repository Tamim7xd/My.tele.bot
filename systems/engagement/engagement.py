# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - معالجة تشغيل الأوامر والأنظمة الحقيقية مباشرة.
"""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank
from systems.engagement.notifications import messages

router = Router(name="engagement")

# ===== بناء قوائم المفاتيح الشفافة للخاص =====

def _member_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
    ])

def _staff_menu_keyboard(rank: str) -> InlineKeyboardMarkup:
    cmd = "ادمن" if rank == "admin" else "مشرف"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="📋 القائمة الإدارية", callback_data=f"eng:cmd:{cmd}")],
    ])

def _owner_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="📋 القائمة الإدارية", callback_data="eng:cmd:admin")],
    ])

# ===== معالج فتح القائمة الدوري للمجموعة =====

@router.callback_query(F.data == "eng:open_menu")
async def open_personal_menu(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    full_name = callback.from_user.full_name
    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

    if user_id == OWNER_ID:
        text = messages.member_menu_text(full_name)
        keyboard = _owner_menu_keyboard()
    elif rank in ("admin", "moderator"):
        text = messages.staff_menu_text(full_name, rank)
        keyboard = _staff_menu_keyboard(rank)
    else:
        text = messages.member_menu_text(full_name)
        keyboard = _member_menu_keyboard()

    try:
        await callback.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        await callback.answer(messages.MENU_OPENED)
    except Exception:
        await callback.answer(messages.NEED_START, show_alert=True)

# ===== المحرك الرئيسي لتشغيل ومعالجة الأوامر الحقيقية للأنظمة الأخرى مباشرة =====

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    cmd_text = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

    # حماية الأزرار الإدارية
    if cmd_text in ("مشرف", "ادمن", "admin"):
        if user_id != OWNER_ID and rank not in ("admin", "moderator"):
            await callback.answer("⚠️ عذراً، هذا الزر مخصص للإدارة فقط.")
            return

    await callback.answer()

    # محاكاة رسالة نصية قادمة من العضو لتشغيل الأنظمة الأخرى
    fake_message = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat, # إرسالها في الشات الحالي (الخاص)
        from_user=callback.from_user,
        text=cmd_text
    )

    # --- 1️⃣ تشغيل نظام معلوماتي القديم (حساب) ---
    if cmd_text == "حساب":
        from systems.members import queries as members_queries
        from systems.members.notifications import messages as member_messages

        member = await members_queries.get_member(pool, user_id)
        if member is None:
            await callback.message.answer("❌ لم يتم تسجيلك بعد.")
            return

        from systems.members import queries as mq
        warnings_count = await mq.get_warnings_count(pool, user_id)
        violations_count = await mq.get_violations_count(pool, user_id)
        active_title_name = None
        membership_name = None

        try:
            from systems.shop import queries as shop_queries
            from systems.shop import member_queries as shop_member_queries

            active_title_id = await shop_member_queries.get_active_title(pool, user_id)
            if active_title_id:
                title = await shop_queries.get_title_by_id(pool, active_title_id)
                if title: active_title_name = title["name"]

            membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
            if membership_status:
                membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
                if membership: membership_name = membership["name"]
        except Exception:
            pass

        text = member_messages.account_card_text(
            full_name=member["full_name"], username=member["username"], level=member["level"],
            messages_count=member["messages_count"], balance=member["balance"], warnings_count=warnings_count,
            violations_count=violations_count, games_played=member["games_played"], games_won=member["games_won"],
            active_title_name=active_title_name, membership_name=membership_name,
        )
        await callback.message.answer(text)

    # --- 2️⃣ تشغيل نظام السوق الحقيقي المتصل بالمتجر لديك (سوق) ---
    elif cmd_text == "سوق":
        try:
            from systems.shop import shop as shop_system
            # استدعاء دالة المعالجة الحقيقية داخل نظام المتجر لديك كأن المستخدم أرسل الكلمة
            if hasattr(shop_system, 'show_shop_menu'):
                await shop_system.show_shop_menu(fake_message)
            elif hasattr(shop_system, 'shop_handler'):
                await shop_system.shop_handler(fake_message)
            else:
                # إذا كان يعتمد على الـ router الرئيسي للسوق نقوم بتمرير التحديث له مباشرة
                await shop_system.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 نظام السوق غير متصل حالياً بالخاص.")

    # --- 3️⃣ تشغيل نظام العضويات الحقيقي (عضويتي) ---
    elif cmd_text == "عضويتي":
        try:
            from systems.shop import shop as shop_system
            await shop_system.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 نظام العضويات غير متصل حالياً بالخاص.")

    # --- 4️⃣ تشغيل نظام الألقاب الحقيقي (مشترياتي) ---
    elif cmd_text == "مشترياتي":
        try:
            from systems.shop import shop as shop_system
            await shop_system.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 نظام إدارة الألقاب غير متصل حالياً بالخاص.")

    # --- 5️⃣ تشغيل نظام الترتيب ولوحة الصدارة (ترتيب) ---
    elif cmd_text == "ترتيب":
        try:
            from systems.wallet import leaderboard
            await leaderboard.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 نظام قائمة المتصدرين غير متصل حالياً بالخاص.")

    # --- 6️⃣ زر القائمة الإدارية المطور (تشغيل أوامر الإشراف والإدارة الحقيقية) ---
    elif cmd_text == "مشرف":
        try:
            from systems.moderators import moderators
            await moderators.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 تعذر فتح لوحة المشرف في الخاص.")

    elif cmd_text == "ادمن":
        try:
            from systems.moderators import moderators
            await moderators.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 تعذر فتح لوحة الأدمن في الخاص.")

    elif cmd_text == "admin":
        try:
            from systems.owner import owner
            await owner.router.feed_webhook_update(callback.bot, fake_message)
        except Exception:
            await callback.message.answer("💬 تعذر فتح لوحة التحكم الرئيسية (admin) في الخاص.")


# ===== مجدول الإرسال الدوري المصلح ذو الاستجابة السريعة =====

async def engagement_scheduler_loop(bot: Bot) -> None:
    while True:
        pool = await get_pool()
        settings = await engagement_queries.get_engagement_settings(pool)
        
        if settings.get("enabled", False) and settings.get("messages"):
            try:
                await _send_engagement_message(bot)
            except Exception:
                pass
            interval = settings.get("interval_seconds", 3600)
            await asyncio.sleep(max(interval, 30))
        else:
            await asyncio.sleep(15)

async def _send_engagement_message(bot: Bot) -> None:
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    if not settings.get("enabled", False) or not settings.get("messages"):
        return

    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)
    if not group_id:
        return

    active_msgs = [m for m in settings["messages"] if m.get("active", True)]
    if not active_msgs:
        return

    idx = settings.get("current_index", 0)
    if idx >= len(active_msgs):
        idx = 0

    current_msg = active_msgs[idx]
    text = current_msg.get("message_text", "")
    
    keyboard = None
    if current_msg.get("button_enabled", True):
        button_text = current_msg.get("button_text", "📋 قائمتي")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="eng:open_menu")]
        ])

    try:
        await bot.send_message(chat_id=group_id, text=text, reply_markup=keyboard)
        await engagement_queries.add_to_engagement_history(pool, text)
        
        settings["current_index"] = (idx + 1) % len(active_msgs)
        await engagement_queries.set_engagement_settings(pool, settings)
    except Exception:
        pass
