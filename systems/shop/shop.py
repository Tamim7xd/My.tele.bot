# -*- coding: utf-8 -*-
"""
نظام المتجر المطور - حظر الأوامر في المجموعات وجعلها تعمل في الخاص فقط.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.database import get_pool

router = Router(name="shop")

# 🚫 قائمة الكلمات والأوامر التي تريد تعطيلها في المجموعات ونقلها للخاص
BLOCKED_KEYWORDS = {"سوق", "المتجر", "عضويتي", "مشترياتي", "ألقابي", "ترتيب"}

# =====================================================================
# 1️⃣ معالج الحظر التلقائي داخل المجموعات (يعترض الكلمات ويعطلها)
# =====================================================================
@router.message(F.chat.type.in_({"group", "supergroup"}) & F.text.in_(BLOCKED_KEYWORDS))
async def block_commands_in_groups(message: Message) -> None:
    # حذف رسالة العضو لكي يبقى شات المجموعة نظيفاً (تتطلب صلاحية حذف الرسائل للبوت)
    try:
        await message.delete()
    except Exception:
        pass
        
    # إرسال تنبيه مؤقت أو رسالة توجيهية للعضو
    msg = await message.answer(
        f"⚠️ عذراً {message.from_user.full_name}، أمر «<b>{message.text}</b>» تم تعطيله داخل المجموعة.\n"
        f"📋 يرجى استخدام <b>زر التفاعل التلقائي الدوري</b> لفتح قائمتك الشخصية وتشغيل الميزة في الخاص مباشرة!"
    )
    
    # حذف تنبيه البوت بعد 5 ثوانٍ تلقائياً لكي لا يتشوه الشات
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass


# =====================================================================
# 2️⃣ معالجات الأوامر الرسمية (تعمل الآن حصرياً داخل الخاص Private Chat)
# =====================================================================

# معالج أمر "سوق" بالخاص
@router.message(F.chat.type == "private" & (Command("سوق") | (F.text == "سوق") | Command("المتجر") | (F.text == "المتجر")))
async def shop_menu_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import queries as shop_queries
    
    # جلب البيانات الحقيقية من متجرك
    settings = await shop_queries.get_shop_settings(pool)
    text = "🛒 <b>سوق البوت الرسمي (الخاص):</b>\n━━━━━━━━━━━━━━━\n"
    # هنا كود صياغة الأسعار والأزرار الأصلية الخاصة بمتجرك...
    await message.answer(text, parse_mode="HTML")


# معالج أمر "عضويتي" بالخاص
@router.message(F.chat.type == "private" & (Command("عضويتي") | (F.text == "عضويتي")))
async def membership_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import member_queries as shop_member_queries
    from systems.shop import queries as shop_queries
    
    membership_status = await shop_member_queries.get_member_membership_status(pool, message.from_user.id)
    if not membership_status:
        await message.answer("👑 لا تمتلك أي عضوية نشطة حالياً. يمكنك الشراء من السوق!")
        return
        
    membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
    await message.answer(f"👑 <b>تفاصيل عضويتك النشطة بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ الاسم: {membership['name']}")


# معالج أمر "مشترياتي / ألقابي" بالخاص
@router.message(F.chat.type == "private" & (Command("مشترياتي") | (F.text == "مشترياتي") | Command("ألقابي") | (F.text == "ألقابي")))
async def titles_private(message: Message) -> None:
    pool = await get_pool()
    from systems.shop import member_queries as shop_member_queries
    from systems.shop import queries as shop_queries
    
    active_title_id = await shop_member_queries.get_active_title(pool, message.from_user.id)
    if not active_title_id:
        await message.answer("🏷️ لا يوجد أي لقب مجهز لحسابك حالياً.")
        return
        
    title = await shop_queries.get_title_by_id(pool, active_title_id)
    await message.answer(f"🏷️ <b>لقبك الحالي النشط:</b> 【 {title['name']} 】")
