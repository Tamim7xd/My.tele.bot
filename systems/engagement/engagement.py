# -*- coding: utf-8 -*-
"""
نظام التفاعل التلقائي المطور (engagement) - يدعم عرض الألقاب كأزرار تبديل تفاعلية بالخاص.
"""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.engagement import queries as engagement_queries
from systems.moderators.permissions import get_user_rank

router = Router(name="engagement")

# ===== لوحات المفاتيح الرئيسية للقائمة الشخصية =====

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

# ===== معالج فتح القائمة الرئيسي =====

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

# ===== المعالج التفاعلي الذكي للأوامر والتبديل المباشر للألقاب =====

@router.callback_query(F.data.startswith("eng:cmd:"))
async def run_command(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    cmd_text = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    pool = await get_pool()
    rank = await get_user_rank(pool, user_id)

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
            await callback.message.answer("❌ لم يتم تسجيلك بعد.")
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

    # --- 2️⃣ زر السوق التفاعلي بالخاص ---
    elif cmd_text == "s_shop" or cmd_text == "سوق":
        try:
            shop_data = await get_setting(pool, "shop_settings", {})
            memberships = shop_data.get("memberships", []) if isinstance(shop_data, dict) else []
            titles = shop_data.get("titles", []) if isinstance(shop_data, dict) else []
            
            text = "🛒 <b>سوق البوت الرسمي المتاح حالياً بالخاص:</b>\n━━━━━━━━━━━━━━━\n"
            kb = []
            if memberships:
                text += "👑 <b>العضويات:</b>\n"
                for m in memberships:
                    text += f"▫️ {m.get('name')} — السعر: <code>{m.get('price')}</code> 🪙\n"
                    kb.append([InlineKeyboardButton(text=f"👑 شراء: {m.get('name')}", callback_data=f"shop:buy_membership:{m.get('id')}")])
            if titles:
                text += "\n🏷️ <b>الألقاب المتاحة:</b>\n"
                for t in titles:
                    text += f"▫️ {t.get('name')} — السعر: <code>{t.get('price')}</code> 🪙\n"
                    kb.append([InlineKeyboardButton(text=f"🏷️ شراء: {t.get('name')}", callback_data=f"shop:buy_title:{t.get('id')}")])
            
            kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="eng:cmd:back_main")])
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        except Exception:
            await callback.message.answer("❌ تعذر تحميل واجهة السوق حالياً.")

    # --- 3️⃣ زر ألقابي المطور (يعرض الألقاب المملوكة كأزرار للتبديل الفوري) ---
    elif cmd_text == "مشترياتي":
        try:
            # جلب كل الألقاب المملوكة للعضو من قاعدة البيانات الحقيقية لديك
            owned_titles = await shop_member_queries.get_member_titles(pool, user_id) or []
            active_title_id = await shop_member_queries.get_active_title(pool, user_id)

            if not owned_titles:
                await callback.message.answer("🏷️ <b>ألقابك الشخصية:</b>\n━━━━━━━━━━━━━━━\n❌ أنت لا تمتلك أي ألقاب حالياً. يمكنك شراؤها من السوق!")
                return

            text = "🏷️ <b>لوحة إدارة ألقابك الشخصية:</b>\n━━━━━━━━━━━━━━━\n💡 اضغط على اسم اللقب أدناه لتجهيزه وتفعيله فوق حسابك فوراً:\n"
            kb = []

            for t_id in owned_titles:
                title_data = await shop_queries.get_title_by_id(pool, t_id)
                if title_data:
                    is_active = (str(t_id) == str(active_title_id))
                    status_emoji = "✅ مجهز" if is_active else "💤 إجعل نشط"
                    text += f"▪️ 【 {title_data['name']} 】 {'(نشط حالياً)' if is_active else ''}\n"
                    
                    # إنشاء زر لكل لقب؛ عند الضغط يرسل تفعيل اللقب الحقيقي لسستم الـ shop
                    kb.append([InlineKeyboardButton(text=f"{title_data['name']} ── {status_emoji}", callback_data=f"eng:set_title:{t_id}")])

            kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="eng:cmd:back_main")])
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        except Exception:
            await callback.message.answer("❌ حدث خطأ أثناء تحميل لوحة الألقاب الخاصة بك.")

    # --- 4️⃣ زر عضويتي التفاعلي بالخاص ---
    elif cmd_text == "عضويتي":
        try:
            membership_status = await shop_member_queries.get_member_membership_status(pool, user_id)
            if not membership_status:
                await callback.message.answer("👑 لا تمتلك أي عضوية نشطة حالياً فوق حسابك المالي.")
                return
            membership = await shop_queries.get_membership_by_id(pool, membership_status["membership_id"])
            
            text = (
                f"👑 <b>تفاصيل عضويتك الحالية بالبوت:</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✨ الرتبة: <b>{membership['name']}</b>\n"
                f"🪙 المكافأة التابعة لها: <code>{membership.get('daily_reward', 0)}</code> 🪙\n"
            )
            kb = [[InlineKeyboardButton(text="🔙 العودة", callback_data="eng:cmd:back_main")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        except Exception:
            pass

    # --- 5️⃣ زر الترتيب ---
    elif cmd_text == "ترتيب":
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT full_name, balance FROM members ORDER BY balance DESC LIMIT 5")
            text = "🏆 <b>قائمة أغنى 5 أعضاء بالبوت حالياً:</b>\n━━━━━━━━━━━━━━━\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx} - {r['full_name']} | الرصيد: <code>{r['balance']:,}</code> د.ع\n"
            kb = [[InlineKeyboardButton(text="🔙 العودة", callback_data="eng:cmd:back_main")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        except Exception:
            pass

    # --- زر العودة للقائمة الرئيسية الإدارية أو العادية ---
    elif cmd_text == "back_main":
        if user_id == OWNER_ID:
            await callback.message.edit_reply_markup(reply_markup=_owner_menu_keyboard())
        elif rank in ("admin", "moderator"):
            await callback.message.edit_reply_markup(reply_markup=_staff_menu_keyboard(rank))
        else:
            await callback.message.edit_reply_markup(reply_markup=_member_menu_keyboard())


# ===== معالج التبديل الفوري والنشط للقب المختار من الأزرار =====

@router.callback_query(F.data.startswith("eng:set_title:"))
async def switch_member_title_instantly(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    title_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    pool = await get_pool()
    
    from systems.shop import member_queries as shop_member_queries
    from systems.shop import queries as shop_queries

    try:
        # استدعاء دالة التجهيز الحقيقية في قاعدة البيانات الخاصة بسستمك
        await shop_member_queries.set_active_title(pool, user_id, int(title_id))
        title_data = await shop_queries.get_title_by_id(pool, int(title_id))
        
        await callback.answer(f"✅ تم تجهيز وارتداء لقب 【 {title_data['name']} 】 بنجاح!", show_alert=True)
        
        # إعادة تحديث واجهة الأزرار فوراً لتظهر علامة الصح المجهزة فوق اللقب الجديد
        owned_titles = await shop_member_queries.get_member_titles(pool, user_id) or []
        text = "🏷️ <b>لوحة إدارة ألقابك الشخصية:</b>\n━━━━━━━━━━━━━━━\n💡 اضغط على اسم اللقب أدناه لتجهيزه وتفعيله فوق حسابك فوراً:\n"
        kb = []

        for t_id in owned_titles:
            t_data = await shop_queries.get_title_by_id(pool, t_id)
            if t_data:
                is_active = (str(t_id) == str(title_id))
                status_emoji = "✅ مجهز" if is_active else "💤 إجعل نشط"
                text += f"▪️ 【 {t_data['name']} 】 {'(نشط حالياً)' if is_active else ''}\n"
                kb.append([InlineKeyboardButton(text=f"{t_data['name']} ── {status_emoji}", callback_data=f"eng:set_title:{t_id}")])

        kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="eng:cmd:back_main")])
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    except Exception:
        await callback.answer("❌ تعذر تبديل اللقب، يرجى المحاولة لاحقاً.")


# ===== مجدول الإرسال الدوري التلقائي المصلح =====

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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data="eng:open_menu")]])

    try:
        await bot.send_message(chat_id=group_id, text=text, reply_markup=keyboard)
        settings["current_index"] = (idx + 1) % len(active_msgs)
        await engagement_queries.set_engagement_settings(pool, settings)
    except Exception:
        pass
