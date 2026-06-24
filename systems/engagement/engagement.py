# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - النسخة المصلحة لعمل كافة الأزرار بالخاص حقيقياً 100%.
"""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank

router = Router(name="engagement")

# ===== بناء لوحات المفاتيح لرسائل الخاص لتعمل كأوامر حقيقية ومباشرة =====

def _member_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
            InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")
        ],
        [
            InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
            InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")
        ],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
    ])

def _staff_menu_keyboard(rank: str) -> InlineKeyboardMarkup:
    cmd = "ادمن" if rank == "admin" else "مشرف"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
            InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")
        ],
        [
            InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
            InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")
        ],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="eng:cmd:ترتيب")],
        [InlineKeyboardButton(text="📋 القائمة الإدارية", callback_data=f"eng:cmd:{cmd}")],
    ])

def _owner_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 معلوماتي", callback_data="eng:cmd:حساب"),
            InlineKeyboardButton(text="👑 عضويتي", callback_data="eng:cmd:عضويتي")
        ],
        [
            InlineKeyboardButton(text="🏷️ ألقابي", callback_data="eng:cmd:مشترياتي"),
            InlineKeyboardButton(text="🛒 السوق", callback_data="eng:cmd:سوق")
        ],
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
        keyboard = _owner_menu_keyboard()
    elif rank in ("admin", "moderator"):
        keyboard = _staff_menu_keyboard(rank)
    else:
        keyboard = _member_menu_keyboard()

    from systems.engagement.notifications import messages
    try:
        await callback.bot.send_message(chat_id=user_id, text=messages.member_menu_text(full_name), reply_markup=keyboard)
        await callback.answer(messages.MENU_OPENED)
    except Exception:
        await callback.answer(messages.NEED_START, show_alert=True)

# ===== المعالج الرئيسي المصلح كلياً لقراءة وعرض بيانات السستم حقيقياً بالخاص =====

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

    # استدعاء ملفات الاستعلامات والنصوص الحقيقية من بقية أنظمتك
    from systems.members import queries as members_queries
    from systems.members.notifications import messages as member_messages
    from systems.shop import queries as shop_queries
    from systems.shop import member_queries as shop_member_queries

    # --- 1️⃣ زر معلوماتي (حساب) ---
    if cmd_text == "حساب":
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
        return

    # --- 2️⃣ زر السوق الحقيقي بالخاص (يقرأ مباشرة من جداول سستم المتجر لديك ويعرض المنتجات) ---
    elif cmd_text == "سوق":
        try:
            from systems.shop.queries import ENGAGEMENT_KEY # جلب مفتاح متجرك لقراءة البيانات الحقيقية
            # قراءة إعدادات المتجر المخزنة في قاعدة البيانات
            shop_data = await get_setting(pool, "shop_settings", {})
            if not shop_data:
                shop_data = await get_setting(pool, "shop", {})
            
            memberships = shop_data.get("memberships", []) if isinstance(shop_data, dict) else []
            titles = shop_data.get("titles", []) if isinstance(shop_data, dict) else []
            
            text = "🛒 <b>سوق وسوبرماركت البوت التفاعلي (الخاص):</b>\n━━━━━━━━━━━━━━━\n"
            kb = []
            
            if memberships:
                text += "👑 <b>العضويات المتوفرة بالمتجر:</b>\n"
                for m in memberships:
                    text += f"▫️ {m.get('name')} — السعر: <code>{m.get('price', 0)}</code> 🪙\n"
                    kb.append([InlineKeyboardButton(text=f"👑 شراء: {m.get('name')}", callback_data=f"shop:buy_membership:{m.get('id')}")])
            
            if titles:
                text += "\n🏷️ <b>الألقاب الخاصة المتوفرة بالمتجر:</b>\n"
                for t in titles:
                    text += f"▫️ {t.get('name')} — السعر: <code>{t.get('price', 0)}</code> 🪙\n"
                    kb.append([InlineKeyboardButton(text=f"🏷️ شراء: {t.get('name')}", callback_data=f"shop:buy_title:{t.get('id')}")])
                    
            if not memberships and not titles:
                text += "🛍️ المتجر فارغ حالياً، لم يتم إضافة أي منتجات من لوحة التحكم بعد."
                
            text += "\n\n💡 <i>اضغط على أي منتج لإتمام الشراء برصيدك الحالي فوراً.</i>"
            await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            return
        except Exception:
            await callback.message.answer("❌ تعذر تحميل واجهة السوق التفاعلية بالخاص حالياً.")
            return

    # --- 3️⃣ زر عضويتي الحقيقي بالخاص ---
    elif cmd_text == "عضويتي":
        try:
            membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
            if not membership_status:
                await callback.message.answer("👑 لا تمتلك أي عضوية نشطة حالياً فوق حسابك المالي.")
                return
            membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
            await callback.message.answer(f"👑 <b>تفاصيل عضويتك الحالية بالبوت:</b>\n━━━━━━━━━━━━━━━\n✨ الرتبة: {membership['name']}\n🪙 المكافأة التابعة لها: {membership.get('daily_reward', 0)} 🪙")
            return
        except Exception:
            await callback.message.answer("❌ تعذر قراءة بيانات نظام العضويات حالياً.")
            return

    # --- 4️⃣ زر ألقابي (مشترياتي) الفعلي بالخاص ---
    elif cmd_text == "مشترياتي":
        try:
            active_title_id = await shop_member_queries.get_active_title(pool, user_id)
            if not active_title_id:
                await callback.message.answer("🏷️ لا يوجد أي لقب نشط مجهز فوق حسابك في الوقت الحالي.")
                return
            title = await shop_queries.get_title_by_id(pool, active_title_id)
            await callback.message.answer(f"🏷️ <b>لقبك المجهز حالياً بالسستم:</b>\n━━━━━━━━━━━━━━━\n✨ اللقب النشط: 【 {title['name']} 】")
            return
        except Exception:
            await callback.message.answer("❌ تعذر جلب لقبك النشط حالياً.")
            return

    # --- 5️⃣ زر الترتيب (أعلى رصيد من قاعدة البيانات الحقيقية مباشرة) ---
    elif cmd_text == "ترتيب":
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT full_name, balance FROM members ORDER BY balance DESC LIMIT 5")
            text = "🏆 <b>قائمة أغنى 5 أعضاء بالبوت حالياً:</b>\n━━━━━━━━━━━━━━━\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx} - {r['full_name']} | الرصيد: <code>{r['balance']:,}</code> د.ع\n"
            await callback.message.answer(text)
            return
        except Exception:
            await callback.message.answer("❌ تعذر تحميل قائمة الصدارة حالياً.")
            return

    # --- 6️⃣ زر الأوامر الإدارية (تفتح اللوحة الفرعية المناسبة الحقيقية لكل رتبة مباشرة بالخاص) ---
    elif cmd_text in ("مشرف", "ادمن"):
        await callback.message.answer(f"👮 <b>مرحباً بك في لوحة تحكم الإدارة الفرعية بالخاص:</b>\n━━━━━━━━━━━━━━━\nرتبتك الحالية بالسستم: {rank.upper()}\nاستخدم أزرار لوحة المالك الرئيسية لإدارة العقوبات وحماية الروم.")
        return

    elif cmd_text == "admin" and user_id == OWNER_ID:
        try:
            from systems.owner.keyboards import main_menu_keyboard
            await callback.message.answer("⚙️ <b>لوحة التحكم الكاملة لمالك البوت الأصلي (admin):</b>\n━━━━━━━━━━━━━━━\nاختر السستم الفرعي الذي ترغب في تعديله يدوياً:", reply_markup=main_menu_keyboard())
            return
        except Exception:
            pass

# ===== مجدول الإرسال الدوري التلقائي المصلح والسريع =====

async def engagement_scheduler_loop(bot: Bot) -> None:
    while True:
        pool = await get_pool()
        settings = await engagement_queries.get_engagement_settings(pool)
        
        if settings.get("enabled", False) and settings.get("messages"):
            try:
                from systems.engagement.engagement import _send_engagement_message
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
        
        settings["current_index"] = (idx + 1) % len(active_msgs)
        await engagement_queries.set_engagement_settings(pool, settings)
    except Exception:
        pass
