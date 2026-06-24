# -*- coding: utf-8 -*-
"""
نظام الإشراف والعقوبات الإدارية المطور (moderators) - مدمج به أمر الإبلاغ المتعدد الصيغ.
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from core.database import get_pool
from systems.moderators.permissions import get_user_rank

router = Router(name="moderators")

# قائمة كافة صيغ الكلمات والأوامر الخاصة بالتبليغ
REPORT_KEYWORDS = {"ابلاغ", "أبلاغ", "إبلاغ", "تبليغ", "بلغ"}

# =====================================================================
# 1️⃣ أمر الإبلاغ السري المتطور (يستقبل كافة الصيغ ويعمل بالرد)
# =====================================================================
@router.message(
    F.chat.type.in_({"group", "supergroup"}) & 
    (Command(list(REPORT_KEYWORDS)) | F.text.in_(REPORT_KEYWORDS))
)
async def report_message_handler(message: Message) -> None:
    # التحقق من وجود رد (Reply)
    if not message.reply_to_message:
        msg = await message.answer("⚠️ يرجى استخدام أمر «<b>إبلاغ</b>» بالرد على الرسالة المخالفة!")
        await asyncio.sleep(4)
        try:
            await message.delete()
            await msg.delete()
        except Exception:
            pass
        return

    pool = await get_pool()
    reporter = message.from_user       
    offender = message.reply_to_message.from_user 
    
    if offender.is_bot:
        await message.answer("❌ لا يمكنك الإبلاغ عن البوتات.")
        return

    # حذف أمر الإبلاغ فوراً لحماية المبلّغ ونظافة الشات
    try:
        await message.delete()
    except Exception:
        pass

    # صياغة نص البلاغ للمشرفين
    report_text = (
        f"🚨 <b>بلاغ جديد من أعضاء المجموعة!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 <b>المُبلِغ:</b> {reporter.full_name} (<code>{reporter.id}</code>)\n"
        f"👤 <b>المخالف:</b> {offender.full_name} (<code>{offender.id}</code>)\n\n"
        f"💬 <b>نص المخالفة:</b>\n"
        f"<i>« {message.reply_to_message.text or 'محتوى غير نصي (صورة/ملف)'} »</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 الانتقال للمخالفة", url=message.reply_to_message.url)]
    ])

    # جلب المشرفين وإرسال البلاغ لهم بالخاص
    try:
        async with pool.acquire() as conn:
            moderators = await conn.fetch("SELECT user_id FROM moderators_list WHERE is_active = TRUE")
            
        for mod in moderators:
            try:
                await message.bot.send_message(chat_id=mod["user_id"], text=report_text, reply_markup=kb)
            except Exception:
                pass
    except Exception:
        pass

    # تأكيد الاستلام المؤقت في الجروب
    confirm_msg = await message.answer(f"✅ شكراً {reporter.first_name}، تم إرسال بلاغك للمشرفين في الخاص بنجاح.")
    await asyncio.sleep(4)
    try:
        await confirm_msg.delete()
    except Exception:
        pass


# =====================================================================
# 2️⃣ أوامر العقوبات الإدارية الأساسية (كتم، حظر، تحذير)
# =====================================================================

# أمر الكتم
@router.message(F.chat.type.in_({"group", "supergroup"}) & (Command("كتم") | (F.text == "كتم")))
async def mute_user_handler(message: Message) -> None:
    pool = await get_pool()
    user_rank = await get_user_rank(pool, message.from_user.id)
    
    if user_rank not in ("admin", "moderator"):
        return 
        
    if not message.reply_to_message:
        await message.answer("⚠️ يرجى استخدام الأمر بالرد على الشخص المطلوب كتمه.")
        return

    target_user = message.reply_to_message.from_user
    try:
        await message.chat.restrict(user_id=target_user.id, permissions=ChatPermissions(can_send_messages=False))
        await message.answer(f"🔒 تم كتم العضو <b>{target_user.full_name}</b> بنجاح بواسطة المشرف.")
    except Exception:
        await message.answer("❌ تعذر تنفيذ أمر الكتم، تأكد من صلاحيات البوت.")


# أمر إلغاء الكتم
@router.message(F.chat.type.in_({"group", "supergroup"}) & (Command("الغاء الكتم") | (F.text == "الغاء الكتم") | (F.text == "إلغاء الكتم")))
async def unmute_user_handler(message: Message) -> None:
    pool = await get_pool()
    user_rank = await get_user_rank(pool, message.from_user.id)
    
    if user_rank not in ("admin", "moderator"):
        return
        
    if not message.reply_to_message:
        await message.answer("⚠️ يرجى استخدام الأمر بالرد على الشخص لإلغاء كتمه.")
        return

    target_user = message.reply_to_message.from_user
    try:
        await message.chat.restrict(
            user_id=target_user.id, 
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        )
        await message.answer(f"🔓 تم إلغاء كتم العضو <b>{target_user.full_name}</b> ويمكنه الكتابة الآن.")
    except Exception:
        pass


# أمر الحظر
@router.message(F.chat.type.in_({"group", "supergroup"}) & (Command("حظر") | (F.text == "حظر")))
async def ban_user_handler(message: Message) -> None:
    pool = await get_pool()
    user_rank = await get_user_rank(pool, message.from_user.id)
    
    if user_rank not in ("admin", "moderator"):
        return
        
    if not message.reply_to_message:
        await message.answer("⚠️ يرجى استخدام الأمر بالرد على الشخص لحظره.")
        return

    target_user = message.reply_to_message.from_user
    try:
        await message.chat.ban(user_id=target_user.id)
        await message.answer(f"🚷 تم حظر وطرد العضو <b>{target_user.full_name}</b> من المجموعة.")
    except Exception:
        pass


# أمر إلغاء الحظر
@router.message(F.chat.type.in_({"group", "supergroup"}) & (Command("الغاء الحظر") | (F.text == "الغاء الحظر") | (F.text == "إلغاء الحظر")))
async def unban_user_handler(message: Message) -> None:
    pool = await get_pool()
    user_rank = await get_user_rank(pool, message.from_user.id)
    
    if user_rank not in ("admin", "moderator"):
        return
        
    if not message.reply_to_message:
        await message.answer("⚠️ يرجى استخدام الأمر بالرد على الرسالة لإلغاء الحظر.")
        return

    target_user = message.reply_to_message.from_user
    try:
        await message.chat.unban(user_id=target_user.id)
        await message.answer(f"✅ تم إلغاء حظر <b>{target_user.full_name}</b> ويمكنه الدخول مجدداً.")
    except Exception:
        pass
