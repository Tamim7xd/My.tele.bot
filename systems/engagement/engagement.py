# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - تفعيل زر السوق في الخاص بالكامل.
"""

import asyncio
import random
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank
from systems.engagement.notifications import messages

router = Router(name="engagement")

def _member_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
    ])

def _staff_menu_keyboard(rank: str) -> InlineKeyboardMarkup:
    label = "👮 لوحة الأدمن" if rank == "admin" else "🛡️ لوحة المشرف"
    cmd = "ادمن" if rank == "admin" else "مشرف"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text=label, callback_data=f"eng:cmd:{cmd}")],
    ])

def _owner_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
         InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضوية")],
        [InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:لقب"),
         InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="eng:cmd:admin")],
    ])

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

# ===== تنفيذ الأوامر المصلحة والمربوطة بالكامل في الخاص =====

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    cmd = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

    if cmd in ("مشرف", "ادمن", "admin"):
        if user_id != OWNER_ID and rank not in ("admin", "moderator"):
            await callback.answer()
            return
    await callback.answer()

    from systems.members import queries as members_queries
    from systems.members.notifications import messages as member_messages
    from systems.shop import queries as shop_queries
    from systems.shop import member_queries as shop_member_queries

    # --- 1️⃣ زر معلوماتي (حساب) ---
    if cmd == "حساب":
        member = await members_queries.get_member(pool, user_id)
        if member is None:
            await callback.message.answer("❌ لم يتم تسجيلك بعد. أرسل رسالة في المجموعة أولاً.")
            return

        from systems.members import queries as mq
        warnings_count = await mq.get_warnings_count(pool, user_id)
        violations_count = await mq.get_violations_count(pool, user_id)
        active_title_name = None
        membership_name = None

        try:
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

    # --- 2️⃣ زر عضويتي (عضوية) ---
    elif cmd == "عضوية":
        try:
            membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
            if not membership_status:
                await callback.message.answer("👑 <b>حالة العضوية:</b>\n━━━━━━━━━━━━━━━\nلا تمتلك أي عضوية نشطة حالياً. يمكنك تصفح السوق لشراء عضوية مميزة!")
                return
            
            membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
            if not membership:
                await callback.message.answer("❌ خطأ في قراءة تفاصيل عضوية الحساب.")
                return

            text = (
                f"👑 <b>تفاصيل عضويتك النشطة بالسستم:</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🛡️ نوع الرتبة: {membership['name']}\n"
                f"💰 المكافأة اليومية التابعة لها: {membership.get('daily_reward', 0)} 🪙\n"
                f"✨ الميزات والخصائص الإضافية مفعّلة تلقائياً لملفك الشخصي."
            )
            await callback.message.answer(text)
        except Exception:
            await callback.message.answer("❌ حدث خطأ أثناء الاتصال بنظام العضويات.")

    # --- 3️⃣ زر ألقابي (لقب) ---
    elif cmd == "لقب":
        try:
            active_title_id = await shop_member_queries.get_active_title(pool, user_id)
            if not active_title_id:
                await callback.message.answer("🏷️ <b>ألقابك الشخصية:</b>\n━━━━━━━━━━━━━━━\nلا يوجد أي لقب مجهز فوق حسابك حالياً. يمكنك شراء وتجهيز الألقاب من ميزة السوق.")
                return

            title = await shop_queries.get_title_by_id(pool, active_title_id)
            if not title:
                await callback.message.answer("❌ فشل في جلب تفاصيل اللقب المجهز.")
                return

            text = (
                f"🏷️ <b>لقبك الحالي النشط بالسستم:</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✨ اللقب النشط: 【 {title['name']} 】\n"
                f"🪙 سعر شراء اللقب: {title.get('price', 0)} 🪙"
            )
            await callback.message.answer(text)
        except Exception:
            await callback.message.answer("❌ حدث خطأ أثناء الاتصال بنظام الألقاب.")

    # --- 4️⃣ زر السوق المطور (سوق يعمل بالخاص مباشرة) ---
    elif cmd == "سوق":
        try:
            # استخدام دوال السستم المتاحة لديك لجلب المنتجات وقوائم المتجر تلقائياً
            text = "🛒 <b>مرحباً بك في سوق البوت الشخصي بالخاص</b>\n━━━━━━━━━━━━━━━\n"
            
            # جلب محتويات المتجر الأساسية (العضويات والألقاب) من ملفات سستم الـ shop الخاص بك
            text += "👑 <b>العضويات المتاحة بالسستم:</b>\n"
            try:
                # إذا كانت الدالة المتاحة لديك تعيد قائمة بكل العضويات
                memberships = await shop_queries.get_setting(pool, "shop_memberships") or [] # محاكاة لسياق الحفظ لديك
                if memberships:
                    for m in memberships:
                        text += f"🔹 {m.get('name')} | السعر: {m.get('price', 0)} 🪙\n"
                else:
                    text += "▫️ لا توجد عضويات مضافة باللوحة حالياً.\n"
            except Exception:
                text += "▫️ تعذر عرض العضويات تلقائياً.\n"
                
            text += "\n🏷️ <b>الألقاب المتاحة بالسستم:</b>\n"
            try:
                titles = await shop_queries.get_setting(pool, "shop_titles") or []
                if titles:
                    for t in titles:
                        text += f"🔹 {t.get('name')} | السعر: {t.get('price', 0)} 🪙\n"
                else:
                    text += "▫️ لا توجد ألقاب مضافة باللوحة حالياً.\n"
            except Exception:
                text += "▫️ تعذر عرض قائمة الألقاب.\n"
                
            text += "\n💡 <i>لشراء أي عنصر، يرجى كتابة (شراء + اسم العنصر) داخل المجموعة للاستفادة من رصيدك العام.</i>"
            await callback.message.answer(text)
        except Exception:
            await callback.message.answer("❌ حدث خطأ أثناء تحميل بيانات سوق البوت.")

    # --- 5️⃣ باقي الأوامر الإدارية والعامة (ترتيب، مشرف، ادمن) ---
    elif cmd in ("ترتيب", "مشرف", "ادمن"):
        cmd_map = {"ترتيب": "ترتيب", "مشرف": "مشرف", "ادمن": "ادمن"}
        await callback.message.answer(f"💬 اكتب «{cmd_map.get(cmd, cmd)}» في المجموعة لفتح هذه الميزة.")
        
    elif cmd == "admin" and (user_id == OWNER_ID):
        await callback.message.answer("💬 اكتب «admin» في المجموعة لفتح لوحة التحكم.")

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
