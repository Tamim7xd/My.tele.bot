"""
لوحة التحكم - نظام الحماية (protection).

يحتوي على:
- 🛡️ الحماية: تبديل كل ميزة (✅/❌) + الكلمات المحظورة + لوحة المحذوفات
- 📝 الكلمات المحظورة: عرض + 🗑️ حذف + ➕ إضافة (نمط rewards)
- 🗑️ لوحة المحذوفات: قائمة الأعضاء -> 5 محذوفات لكل صفحة -> ⚠️ تحذير / 🔇 كتم
- من صفحة العضو (👥 الأعضاء): 🛡️ استثناءات الحماية الفردية

تم التعديل: إضافة دعم جهات الاتصال + إصلاح الاستثناءات + تحسين الأداء.
"""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool, get_setting
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.members import queries as members_queries
from systems.moderation import queries as moderation_queries
from systems.protection import queries as protection_queries
from systems.protection import keyboards as prot_keyboards
from systems.protection.notifications import messages


router = Router(name="owner_protection")
logger = logging.getLogger(__name__)


def _is_owner(user_id: int | None) -> bool:
    """التحقق من أن المستخدم هو المالك."""
    return user_id is not None and user_id == OWNER_ID


# ==================== الإعدادات العامة ====================

@router.callback_query(F.data == "owner:protection")
async def show_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """عرض إعدادات الحماية العامة."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض الإعدادات: {e}")
        await callback.message.answer(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_toggle:"))
async def toggle_feature(callback: CallbackQuery) -> None:
    """تبديل حالة ميزة معينة (تشغيل/إيقاف)."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    feature_key = callback.data.split(":")[-1]

    pool = await get_pool()
    new_state = await protection_queries.toggle_feature(pool, feature_key)

    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    # رسالة تأكيد قصيرة
    status = "✅ تم التفعيل" if new_state else "❌ تم الإيقاف"
    feature_label = protection_queries.FEATURE_LABELS.get(feature_key, feature_key)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(f"{status} لـ {feature_label}", show_alert=False)


# ==================== الكلمات المحظورة ====================

@router.callback_query(F.data.startswith("owner:prot_words:"))
async def show_banned_words(callback: CallbackQuery, state: FSMContext) -> None:
    """عرض قائمة الكلمات المحظورة مع إمكانية التصفح."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])
    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    words = settings.get("banned_words", [])

    # التأكد من أن offset في النطاق الصحيح
    if offset >= len(words) and len(words) > 0:
        offset = max(0, len(words) - 10)

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, offset)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض الكلمات المحظورة: {e}")
        await callback.message.answer(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_word_remove:"))
async def remove_banned_word(callback: CallbackQuery) -> None:
    """حذف كلمة من قائمة الكلمات المحظورة."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    # استخراج الكلمة (قد تحتوي على : لذلك نستخدم split مع حد أقصى)
    word = callback.data.split(":", 2)[-1]

    pool = await get_pool()
    words = await protection_queries.remove_banned_word(pool, word)

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.word_removed_text(word), show_alert=False)


@router.callback_query(F.data == "owner:prot_word_add")
async def add_banned_word_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    """طلب إدخال كلمة جديدة للحظر."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_protection_word)

    await callback.message.edit_text(
        messages.ADD_WORD_PROMPT,
        reply_markup=prot_keyboards.cancel_keyboard(),
    )
    await callback.answer()


@router.message(OwnerStates.waiting_protection_word)
async def add_banned_word_receive(message: Message, state: FSMContext) -> None:
    """استلام كلمة جديدة وإضافتها للقائمة."""
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None or not message.text.strip():
        await message.reply("❌ الرجاء إرسال كلمة صالحة.")
        return

    word = message.text.strip().lower()

    # منع الكلمات الطويلة جداً
    if len(word) > 50:
        await message.reply("❌ الكلمة طويلة جداً (الحد الأقصى 50 حرفاً).")
        return

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    existing_words = settings.get("banned_words", [])

    if word in existing_words:
        await message.reply(
            messages.ADD_WORD_DUPLICATE,
            reply_markup=prot_keyboards.cancel_keyboard(),
        )
        return

    words = await protection_queries.add_banned_word(pool, word)
    await state.clear()

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await message.reply(messages.word_added_text(word), reply_markup=keyboard)


# ==================== لوحة المحذوفات ====================

@router.callback_query(F.data == "owner:prot_deleted")
async def show_deleted_main(callback: CallbackQuery, state: FSMContext) -> None:
    """عرض لوحة المحذوفات الرئيسية."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    violators_count = await protection_queries.get_violators_with_logs_count(pool)

    text = messages.deleted_main_text(violators_count)
    keyboard = prot_keyboards.deleted_main_keyboard(violators_count)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض لوحة المحذوفات: {e}")
        await callback.message.answer(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_list:"))
async def show_deleted_list(callback: CallbackQuery) -> None:
    """عرض قائمة الأعضاء المخالفين."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    pool = await get_pool()
    total = await protection_queries.get_violators_with_logs_count(pool)
    
    if total == 0:
        await callback.answer("لا يوجد مخالفين حالياً", show_alert=True)
        return
    
    violators = await protection_queries.get_violators_with_logs_list(pool, offset=offset, limit=6)

    members_data = [(v["user_id"], v["username"], v["full_name"], v["deleted_count"]) for v in violators]

    text = messages.deleted_list_text(total)
    keyboard = prot_keyboards.deleted_list_keyboard(members_data, offset, total, limit=6)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_member:"))
async def show_member_deleted(callback: CallbackQuery) -> None:
    """عرض محذوفات عضو معين."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("خطأ في البيانات")
        return

    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    await _render_member_deleted(callback, user_id, page)


async def _render_member_deleted(callback: CallbackQuery, user_id: int, page: int) -> None:
    """عرض محذوفات عضو معين (دالة مساعدة)."""
    pool = await get_pool()

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer("❌ العضو غير موجود في قاعدة البيانات")
        return

    total = await protection_queries.get_member_deleted_count(pool, user_id)
    
    if total == 0:
        await callback.answer("لا يوجد محذوفات لهذا العضو", show_alert=True)
        return
    
    entries = await protection_queries.get_member_deleted_entries(pool, user_id, offset=page * 5, limit=5)

    text = messages.member_deleted_text(member["full_name"], entries, total)
    keyboard = prot_keyboards.member_deleted_keyboard(user_id, page, total, limit=5)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض محذوفات العضو: {e}")
    
    await callback.answer()


# ==================== إجراءات من لوحة المحذوفات ====================

@router.callback_query(F.data.startswith("owner:prot_del_warn:"))
async def deleted_warn(callback: CallbackQuery) -> None:
    """تحذير عضو من لوحة المحذوفات."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("خطأ في البيانات")
        return

    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    pool = await get_pool()

    # تسجيل التحذير في الأرشيف
    await moderation_queries.log_archive_entry(
        pool, 
        user_id=user_id, 
        action_type="warn", 
        reason="تحذير من لوحة المحذوفات (نظام الحماية)", 
        replied_message=None, 
        done_by=callback.from_user.id,
    )

    # محاولة إرسال تحذير للعضو (اختياري)
    try:
        await callback.bot.send_message(
            user_id,
            "⚠️ تنبيه: تم تسجيل مخالفات متكررة بحقك. الرجاء الالتزام بقوانين المجموعة."
        )
    except Exception:
        pass  # العضو قد يكون حظر البوت

    await callback.answer(messages.WARN_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


@router.callback_query(F.data.startswith("owner:prot_del_mute:"))
async def deleted_mute(callback: CallbackQuery) -> None:
    """كتم عضو من لوحة المحذوفات لمدة 10 دقائق."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("خطأ في البيانات")
        return

    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    pool = await get_pool()

    # كتم لمدة 10 دقائق
    mute_duration_seconds = 10 * 60
    until = moderation_queries.duration_to_datetime(mute_duration_seconds)
    await moderation_queries.set_mute(pool, user_id, until)

    # تطبيق الكتم في المجموعة
    from systems.members.members import GROUP_ID_KEY
    group_id = await get_setting(pool, GROUP_ID_KEY)

    if group_id:
        try:
            from aiogram.types import ChatPermissions
            await callback.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
        except Exception as e:
            logger.warning(f"فشل كتم العضو {user_id} في المجموعة: {e}")

    # تسجيل في الأرشيف
    await moderation_queries.log_archive_entry(
        pool,
        user_id=user_id,
        action_type="mute",
        reason=f"كتم تلقائي من لوحة المحذوفات لمدة {mute_duration_seconds // 60} دقيقة",
        replied_message=None,
        done_by=callback.from_user.id,
    )

    await callback.answer(messages.MUTE_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


# ==================== استثناءات فردية لعضو ====================

@router.callback_query(F.data.startswith("owner:prot_exc:"))
async def show_member_exceptions(callback: CallbackQuery) -> None:
    """عرض استثناءات الحماية لعضو معين."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("خطأ في البيانات")
        return

    user_id = int(parts[3])
    offset = int(parts[4]) if len(parts) > 4 else 0

    pool = await get_pool()
    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer("❌ العضو غير موجود")
        return

    exceptions = await protection_queries.get_member_exceptions(pool, user_id)

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض استثناءات العضو: {e}")
    
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_exc_toggle:"))
async def toggle_member_exception(callback: CallbackQuery) -> None:
    """تبديل استثناء عضو لميزة معينة."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer("خطأ في البيانات")
        return

    user_id = int(parts[3])
    offset = int(parts[4])
    feature_key = parts[5]

    pool = await get_pool()
    
    # تبديل الاستثناء
    new_exempt_state = await protection_queries.toggle_member_exception(pool, user_id, feature_key)

    # جلب بيانات العضو للتأكيد
    member = await members_queries.get_member(pool, user_id)
    exceptions = await protection_queries.get_member_exceptions(pool, user_id)
    
    feature_label = protection_queries.FEATURE_LABELS.get(feature_key, feature_key)

    # رسالة تأكيد
    if new_exempt_state:
        confirm_msg = f"✅ تم استثناء {member['full_name']} من {feature_label}\nأصبح بإمكانه تجاوز الحظر العام لهذه الميزة."
    else:
        confirm_msg = f"❌ تم إلغاء استثناء {member['full_name']} من {feature_label}\nأصبح يخضع للإعدادات العامة."

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(confirm_msg, show_alert=False)


@router.callback_query(F.data == "owner:prot_exc_help")
async def show_exceptions_help(callback: CallbackQuery) -> None:
    """عرض مساعدة حول الاستثناءات."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    help_text = """
🛡️ <b>ما هي استثناءات الحماية؟</b>

<b>الاستثناء</b> يعني أن العضو <b>مسموح له</b> بتجاوز الحظر العام لميزة معينة.

<b>مثال:</b>
- إذا كانت "الصور" محظورة عامة ✅
- لكن العضو لديه استثناء ✅ للصور
- يصبح بإمكانه نشر الصور رغم الحظر العام

<b>كيف تعمل؟</b>
• ✅ = العضو مستثنى (مسموح له)
• ❌ = العضو غير مستثنى (يخضع للإعداد العام)

<b>تنبيه:</b>
الاستثناءات لا تؤثر على صلاحيات الأدمن/المشرف - هم معفيون تلقائياً.
"""

    keyboard = prot_keyboards.exceptions_help_keyboard(
        user_id=0,  # سيتم استخراجها من الـ callback context
        offset=0
    )
    
    # نحتاج لاستخراج user_id من آخر رسالة أو تخزينه مؤقتاً
    # لهذا نستخدم طريقة بديلة: حفظ البيانات في رسالة المساعدة

    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()


# ==================== مساعدة إضافية ====================

@router.callback_query(F.data == "owner:protection_help")
async def show_protection_help(callback: CallbackQuery) -> None:
    """عرض مساعدة عامة لنظام الحماية."""
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    help_text = messages.HELP_TEXT
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع للإعدادات", callback_data="owner:protection")],
            [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="owner:main")],
        ]
    )

    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()