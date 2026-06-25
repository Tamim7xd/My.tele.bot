# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - النسخة المصححة والعاملة بكامل الطاقة.
"""

import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank
from systems.engagement.notifications import messages

logger = logging.getLogger(__name__)
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

# ===== معالج فتح القائمة =====

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
    except Exception as e:
        logger.error(f"خطأ في فتح القائمة: {e}")
        await callback.answer(messages.NEED_START, show_alert=True)

# ===== المحرك الرئيسي لمعالجة الأوامر =====

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery) -> None:
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

    try:
        # --- 1️⃣ زر معلوماتي (حساب) ---
        if cmd_text == "حساب":
            await _handle_account_command(callback, pool, user_id)

        # --- 2️⃣ زر السوق ---
        elif cmd_text == "سوق":
            await _handle_shop_command(callback, pool)

        # --- 3️⃣ زر عضويتي ---
        elif cmd_text == "عضويتي":
            await _handle_membership_command(callback, pool, user_id)

        # --- 4️⃣ زر ألقابي (مشترياتي) ---
        elif cmd_text == "مشترياتي":
            await _handle_titles_command(callback, pool, user_id)

        # --- 5️⃣ زر الترتيب ---
        elif cmd_text == "ترتيب":
            await _handle_leaderboard_command(callback, pool)

        # --- 6️⃣ الأوامر الإدارية ---
        elif cmd_text == "مشرف":
            await callback.message.answer("👮 <b>مرحباً بك في لوحة تحكم المشرفين:</b>\n━━━━━━━━━━━━━━━\nاستخدم أوامر المشرفين للتحكم في المجموعة.")

        elif cmd_text == "ادمن":
            await callback.message.answer("🛡️ <b>مرحباً بك في لوحة تحكم الإدارة:</b>\n━━━━━━━━━━━━━━━\nلديك صلاحيات إدارية كاملة.")

        elif cmd_text == "admin":
            await callback.message.answer("⚙️ <b>لوحة التحكم الكاملة لمالك البوت:</b>\n━━━━━━━━━━━━━━━\nأنت المالك - لك جميع الصلاحيات.")

    except Exception as e:
        logger.error(f"خطأ في معالجة الأمر {cmd_text}: {e}")
        await callback.message.answer(f"❌ خطأ: {str(e)[:100]}")

# ===== معالجات الأوامر الفردية =====

async def _handle_account_command(callback: CallbackQuery, pool, user_id: int) -> None:
    """عرض معلومات الحساب"""
    from systems.members import queries as members_queries
    from systems.members.notifications import messages as member_messages
    from systems.shop import queries as shop_queries
    from systems.shop import member_queries as shop_member_queries

    member = await members_queries.get_member(pool, user_id)
    if member is None:
        await callback.message.answer("❌ لم يتم تسجيلك بعد. أرسل رسالة في المجموعة أولاً.")
        return

    warnings_count = await members_queries.get_warnings_count(pool, user_id)
    violations_count = await members_queries.get_violations_count(pool, user_id)
    active_title_name = None
    membership_name = None

    try:
        active_title_id = await shop_member_queries.get_active_title(pool, user_id)
        if active_title_id:
            title = await shop_queries.get_title_by_id(pool, active_title_id)
            if title:
                active_title_name = title["name"]

        membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
        if membership_status:
            membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
            if membership:
                membership_name = membership["name"]
    except Exception as e:
        logger.warning(f"خطأ في جلب البيانات الإضافية: {e}")

    text = member_messages.account_card_text(
        full_name=member["full_name"],
        username=member["username"],
        level=member["level"],
        messages_count=member["messages_count"],
        balance=member["balance"],
        warnings_count=warnings_count,
        violations_count=violations_count,
        games_played=member["games_played"],
        games_won=member["games_won"],
        active_title_name=active_title_name,
        membership_name=membership_name,
    )
    await callback.message.answer(text)

async def _handle_shop_command(callback: CallbackQuery, pool) -> None:
    """عرض السوق"""
    from systems.shop import queries as shop_queries

    try:
        settings = await shop_queries.get_setting(pool, "shop_settings") or {}
        memberships = settings.get("memberships", [])
        titles = settings.get("titles", [])

        text = "🛒 <b>سوق البوت الرسمي المتاح حالياً:</b>\n━━━━━━━━━━━━━━━\n"
        kb = []

        if memberships:
            text += "👑 <b>العضويات المتاحة:</b>\n"
            for m in memberships:
                text += f"▪️ {m['name']} — السعر: <code>{m['price']}</code> 🪙\n"
                kb.append([InlineKeyboardButton(text=f"👑 شراء: {m['name']}", callback_data=f"shop:buy_membership:{m['id']}")])

        if titles:
            text += "\n🏷️ <b>الألقاب المتاحة:</b>\n"
            for t in titles:
                text += f"▪️ {t['name']} — السعر: <code>{t['price']}</code> 🪙\n"
                kb.append([InlineKeyboardButton(text=f"🏷️ شراء: {t['name']}", callback_data=f"shop:buy_title:{t['id']}")])

        text += "\nإضغط على أي زر أدناه لإتمام عملية الشراء فوراً برصيدك."
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb) if kb else None)
    except Exception as e:
        logger.error(f"خطأ في عرض السوق: {e}")
        await callback.message.answer("❌ تعذر تحميل قائمة معروضات السوق حالياً.")

async def _handle_membership_command(callback: CallbackQuery, pool, user_id: int) -> None:
    """عرض العضوية الحالية"""
    from systems.shop import queries as shop_queries
    from systems.shop import member_queries as shop_member_queries

    try:
        membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
        if not membership_status:
            await callback.message.answer("👑 لا تمتلك أي عضوية نشطة حالياً فوق حسابك.")
            return
        membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
        if not membership:
            await callback.message.answer("❌ خطأ في جلب بيانات العضوية.")
            return
        text = f"👑 <b>تفاصيل عضويتك الحالية:</b>\n━━━━━━━━━━━━━━━\n✨ الرتبة: <b>{membership['name']}</b>\n🪙 السعر الأصلي: <code>{membership['price']}</code> 🪙"
        await callback.message.answer(text)
    except Exception as e:
        logger.error(f"خطأ في عرض العضوية: {e}")
        await callback.message.answer("❌ خطأ أثناء قراءة نظام العضويات.")

async def _handle_titles_command(callback: CallbackQuery, pool, user_id: int) -> None:
    """عرض الألقاب المشتراة"""
    from systems.shop import queries as shop_queries
    from systems.shop import member_queries as shop_member_queries

    try:
        active_title_id = await shop_member_queries.get_active_title(pool, user_id)
        if not active_title_id:
            await callback.message.answer("🏷️ لا يوجد أي لقب مجهز لحسابك في الوقت الحالي.")
            return
        title = await shop_queries.get_title_by_id(pool, active_title_id)
        if not title:
            await callback.message.answer("❌ خطأ في جلب بيانات اللقب.")
            return
        text = f"🏷️ <b>لقبك المجهز حالياً بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ اللقب: <b>【 {title['name']} 】</b>\n🪙 السعر: <code>{title['price']}</code> 🪙"
        await callback.message.answer(text)
    except Exception as e:
        logger.error(f"خطأ في عرض الألقاب: {e}")
        await callback.message.answer("❌ خطأ أثناء قراءة سستم الألقاب.")

async def _handle_leaderboard_command(callback: CallbackQuery, pool) -> None:
    """عرض قائمة الصدارة"""
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT full_name, balance FROM members ORDER BY balance DESC LIMIT 5")
        text = "🏆 <b>قائمة أغنى 5 أعضاء بالبوت حالياً:</b>\n━━━━━━━━━━━━━━━\n"
        for idx, r in enumerate(rows, 1):
            text += f"{idx} - {r['full_name']} | الرصيد: <code>{r['balance']}</code> 🪙\n"
        await callback.message.answer(text)
    except Exception as e:
        logger.error(f"خطأ في عرض الترتيب: {e}")
        await callback.message.answer("❌ تعذر جلب قائمة الصدارة حالياً.")

# ===== مجدول الإرسال الدوري =====

async def engagement_scheduler_loop(bot: Bot) -> None:
    """مجدول إرسال الرسائل التفاعلية الدورية"""
    logger.info("🔄 بدء مجدول التفاعل التلقائي...")
    
    while True:
        try:
            pool = await get_pool()
            settings = await engagement_queries.get_engagement_settings(pool)

            if settings.get("enabled", False) and settings.get("messages"):
                await _send_engagement_message(bot, pool, settings)
                interval = settings.get("interval_seconds", 3600)
                await asyncio.sleep(max(interval, 30))
            else:
                await asyncio.sleep(15)
        except Exception as e:
            logger.error(f"خطأ في مجدول التفاعل: {e}")
            await asyncio.sleep(15)

async def _send_engagement_message(bot: Bot, pool, settings: dict) -> None:
    """إرسال رسالة تفاعلية واحدة"""
    try:
        if not settings.get("enabled", False) or not settings.get("messages"):
            return

        from systems.members.members import GROUP_ID_KEY
        group_id = await get_setting(pool, GROUP_ID_KEY)
        if not group_id:
            logger.warning("لم يتم تعيين معرّف المجموعة")
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

        await bot.send_message(chat_id=group_id, text=text, reply_markup=keyboard)
        await engagement_queries.add_to_engagement_history(pool, text)

        settings["current_index"] = (idx + 1) % len(active_msgs)
        await engagement_queries.set_engagement_settings(pool, settings)
        
        logger.info(f"✅ تم إرسال رسالة التفاعل #{idx + 1}")
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة التفاعل: {e}")
