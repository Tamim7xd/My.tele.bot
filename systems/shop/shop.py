# -*- coding: utf-8 -*-
"""
نظام المتجر المطور والمصلح - حظر الأوامر في المجموعات وجعلها تعمل في الخاص فقط 100%.
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_pool

router = Router(name="shop")

# قائمة الكلمات والأوامر التي سيتم مسحها وحظرها تلقائياً داخل المجموعات ليبقى الشات نظيفاً
BLOCKED_KEYWORDS = ["سوق", "المتجر", "عضويتي", "مشترياتي", "ألقابي", "ترتيب"]

# =====================================================================
# 1️⃣ معالج الحظر الذكي والتنظيف التلقائي داخل المجموعات
# =====================================================================
@router.message(F.chat.type.in_({"group", "supergroup"}) and F.text.in_(BLOCKED_KEYWORDS))
async def block_commands_in_groups(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass
        
    try:
        msg = await message.answer(
            f"⚠️ عذراً {message.from_user.full_name}، أمر «<b>{message.text}</b>» معطّل داخل المجموعة.\n"
            f"📋 إضغط على زر التفاعل التلقائي الدوري لتشغيل الميزة في الخاص مباشرة!"
        )
        await asyncio.sleep(5)
        await msg.delete()
    except Exception:
        pass


# =====================================================================
# 2️⃣ معالجات الأوامر الرسمية الفعالة حصرياً داخل محادثة الخاص (Private Chat)
# =====================================================================

# دالة فتح "السوق" بالخاص
async def shop_menu_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import queries as shop_queries
    
    try:
        # جلب الإعدادات الحقيقية المخزنة بنظام المتجر لديك
        settings = await shop_queries.get_setting(pool, "shop_settings") or {}
        memberships = settings.get("memberships", [])
        titles = settings.get("titles", [])
        
        text = "🛒 <b>سوق وسوبرماركت البوت التفاعلي (الخاص):</b>\n━━━━━━━━━━━━━━━\n"
        kb = []
        
        if memberships:
            text += "👑 <b>العضويات المتوفرة بالمتجر:</b>\n"
            for m in memberships:
                text += f"▫️ {m['name']} — السعر: <code>{m['price']}</code> 🪙\n"
                kb.append([InlineKeyboardButton(text=f"👑 شراء: {m['name']}", callback_data=f"shop:buy_membership:{m['id']}")])
        
        if titles:
            text += "\n🏷️ <b>الألقاب الخاصة المتوفرة بالمتجر:</b>\n"
            for t in titles:
                text += f"▫️ {t['name']} — السعر: <code>{t['price']}</code> 🪙\n"
                kb.append([InlineKeyboardButton(text=f"🏷️ شراء: {t['name']}", callback_data=f"shop:buy_title:{t['id']}")])
                
        text += "\n💡 <i>اضغط على أي منتج لإتمام الشراء برصيدك الحالي فوراً.</i>"
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    except Exception:
        await message.answer("❌ تعذر فتح قائمة معروضات السوق بالخاص حالياً.")

@router.message(F.chat.type == "private" and (Command("سوق") | (F.text == "سوق") | Command("المتجر") | (F.text == "المتجر")))
async def shop_command_handler(message: Message) -> None:
    await shop_menu_private(message)


# دالة فتح "عضويتي" بالخاص
async def membership_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import member_queries as shop_member_queries
    from systems.shop import queries as shop_queries
    
    try:
        membership_status = await shop_member_queries.get_member_membership_status(pool, message.from_user.id)
        if not membership_status:
            await message.answer("👑 لا تمتلك أي عضوية نشطة حالياً فوق حسابك المالي.")
            return
            
        membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
        await message.answer(f"👑 <b>تفاصيل عضويتك النشطة بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ الاسم: {membership['name']}\n🪙 المكافأة اليومية: {membership.get('daily_reward', 0)} 🪙")
    except Exception:
        await message.answer("❌ خطأ أثناء جلب تفاصيل نظام العضويات.")

@router.message(F.chat.type == "private" and (Command("عضويتي") | (F.text == "عضويتي")))
async def membership_command_handler(message: Message) -> None:
    await membership_private(message)


# دالة فتح "ألقابي" بالخاص
async def titles_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import member_queries as shop_member_queries
    from systems.shop import queries as shop_queries
    
    try:
        active_title_id = await shop_member_queries.get_active_title(pool, message.from_user.id)
        if not active_title_id:
            await message.answer("🏷️ لا يوجد أي لقب مجهز لحسابك حالياً بالخاص.")
            return
            
        title = await shop_queries.get_title_by_id(pool, active_title_id)
        await message.answer(f"🏷️ <b>لقبك الحالي النشط بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ اللقب النشط: 【 {title['name']} 】")
    except Exception:
        await message.answer("❌ خطأ أثناء جلب قائمة الألقاب الخاصة بك.")

@router.message(F.chat.type == "private" and (Command("مشترياتي") | (F.text == "مشترياتي") | Command("ألقابي") | (F.text == "ألقابي")))
async def titles_command_handler(message: Message) -> None:
    await titles_private(message)
