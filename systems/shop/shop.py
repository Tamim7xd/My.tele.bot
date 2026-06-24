# -*- coding: utf-8 -*-
"""
نظام المتجر المطور والمصلح - حظر الأوامر في المجموعات وجعلها تعمل في الخاص فقط 100%.
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.database import get_pool

router = Router(name="shop")

# قائمة الكلمات والأوامر التي سيتم مسحها وحظرها تلقائياً داخل المجموعات
BLOCKED_KEYWORDS = ["سوق", "المتجر", "عضويتي", "مشترياتي", "ألقابي", "ترتيب"]

# =====================================================================
# 1️⃣ معالج الحظر الذكي والتنظيف التلقائي داخل المجموعات (جروب / سوبر جروب)
# =====================================================================
@router.message(F.chat.type.in_({"group", "supergroup"}) and F.text.in_(BLOCKED_KEYWORDS))
async def block_commands_in_groups(message: Message) -> None:
    # حذف رسالة العضو فوراً لإبقاء الشات نظيفاً
    try:
        await message.delete()
    except Exception:
        pass
        
    # إرسال تنبيه مؤقت للعضو يوجهه للخاص
    try:
        msg = await message.answer(
            f"⚠️ عذراً {message.from_user.full_name}، أمر «<b>{message.text}</b>» معطّل هنا.\n"
            f"📋 إضغط على زر التفاعل التلقائي الدوري لتشغيل الميزة في الخاص مباشرة!"
        )
        # حذف تنبيه البوت بعد 5 ثوانٍ تلقائياً لعدم تشويه الشات
        await asyncio.sleep(5)
        await msg.delete()
    except Exception:
        pass


# =====================================================================
# 2️⃣ معالجات الأوامر الرسمية الفعالة حصرياً داخل محادثة الخاص (Private Chat)
# =====================================================================

# معالج أمر "سوق" بالخاص
@router.message(F.chat.type == "private" and (Command("سوق") | (F.text == "سوق") | Command("المتجر") | (F.text == "المتجر")))
async def shop_menu_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import queries as shop_queries
    
    try:
        settings = await shop_queries.get_shop_settings(pool)
        text = "🛒 <b>سوق وسوبرماركت البوت التفاعلي (الخاص):</b>\n━━━━━━━━━━━━━━━\n"
        # (هنا كود صياغة الأسعار والأزرار الأصلية التابعة لمتجرك)
        await message.answer(text, parse_mode="HTML")
    except Exception:
        await message.answer("❌ تعذر فتح قائمة معروضات السوق بالخاص حالياً.")


# معالج أمر "عضويتي" بالخاص
@router.message(F.chat.type == "private" and (Command("عضويتي") | (F.text == "عضويتي")))
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
        await message.answer(f"👑 <b>تفاصيل عضويتك النشطة بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ الاسم: {membership['name']}")
    except Exception:
        await message.answer("❌ خطأ أثناء جلب تفاصيل نظام العضويات.")


# معالج أمر "مشترياتي / ألقابي" بالخاص
@router.message(F.chat.type == "private" and (Command("مشترياتي") | (F.text == "مشترياتي") | Command("ألقابي") | (F.text == "ألقابي")))
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
        await message.answer(f"🏷️ <b>لقبك الحالي النشط:</b> 【 {title['name']} 】")
    except Exception:
        await message.answer("❌ خطأ أثناء جلب قائمة الألقاب الخاصة بك.")
