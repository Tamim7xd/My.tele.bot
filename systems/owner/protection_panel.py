"""
لوحة التحكم - نظام الحماية (مع إصلاح الاستثناءات)
"""

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
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
    return user_id is not None and user_id == OWNER_ID


# ==================== الإعدادات العامة ====================

@router.callback_query(F.data == "owner:protection")
async def show_settings(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_toggle:"))
async def toggle_feature(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    feature_key = callback.data.split(":")[-1]

    pool = await get_pool()
    new_state = await protection_queries.toggle_feature(pool, feature_key)

    settings = await protection_queries.get_protection_settings(pool)

    text = messages.settings_text(settings)
    keyboard = prot_keyboards.settings_keyboard(settings)

    await callback.message.edit_text(text, reply_markup=keyboard)
    
    status = "✅ تم التفعيل" if new_state else "❌ تم الإيقاف"
    feature_label = protection_queries.FEATURE_LABELS.get(feature_key, feature_key)
    await callback.answer(f"{status} لـ {feature_label}")


# ==================== الكلمات المحظورة ====================

@router.callback_query(F.data.startswith("owner:prot_words:"))
async def show_banned_words(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])
    await state.clear()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    words = settings.get("banned_words", [])

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_word_remove:"))
async def remove_banned_word(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    word = callback.data.split(":", 2)[-1]

    pool = await get_pool()
    words = await protection_queries.remove_banned_word(pool, word)

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(messages.word_removed_text(word))


@router.callback_query(F.data == "owner:prot_word_add")
async def add_banned_word_prompt(callback: CallbackQuery, state: FSMContext) -> None:
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
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if message.text is None or not message.text.strip():
        await message.reply("❌ الرجاء إرسال كلمة صالحة.")
        return

    word = message.text.strip().lower()

    pool = await get_pool()
    settings = await protection_queries.get_protection_settings(pool)
    existing_words = settings.get("banned_words", [])

    if word in existing_words:
        await message.reply(messages.ADD_WORD_DUPLICATE)
        return

    words = await protection_queries.add_banned_word(pool, word)
    await state.clear()

    text = messages.banned_words_text(words)
    keyboard = prot_keyboards.banned_words_keyboard(words, 0)

    await message.reply(messages.word_added_text(word), reply_markup=keyboard)


# ==================== لوحة المحذوفات ====================

@router.callback_query(F.data == "owner:prot_deleted")
async def show_deleted_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    violators_count = await protection_queries.get_violators_with_logs_count(pool)

    text = messages.deleted_main_text(violators_count)
    keyboard = prot_keyboards.deleted_main_keyboard(violators_count)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_list:"))
async def show_deleted_list(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    offset = int(callback.data.split(":")[-1])

    pool = await get_pool()
    total = await protection_queries.get_violators_with_logs_count(pool)
    violators = await protection_queries.get_violators_with_logs_list(pool, offset=offset, limit=6)

    members_data = [(v["user_id"], v["username"], v["full_name"], v["deleted_count"]) for v in violators]

    text = messages.deleted_list_text(total)
    keyboard = prot_keyboards.deleted_list_keyboard(members_data, offset, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_member:"))
async def show_member_deleted(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    await _render_member_deleted(callback, user_id, page)


async def _render_member_deleted(callback: CallbackQuery, user_id: int, page: int) -> None:
    pool = await get_pool()

    member = await members_queries.get_member(pool, user_id)

    if member is None:
        await callback.answer("❌ العضو غير موجود في قاعدة البيانات")
        return

    total = await protection_queries.get_member_deleted_count(pool, user_id)
    entries = await protection_queries.get_member_deleted_entries(pool, user_id, offset=page * 5, limit=5)

    text = messages.member_deleted_text(member["full_name"], entries, total)
    keyboard = prot_keyboards.member_deleted_keyboard(user_id, page, total)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_del_warn:"))
async def deleted_warn(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    pool = await get_pool()

    await moderation_queries.log_archive_entry(
        pool, user_id=user_id, action_type="warn", 
        reason=None, replied_message=None, done_by=callback.from_user.id,
    )

    await callback.answer(messages.WARN_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


@router.callback_query(F.data.startswith("owner:prot_del_mute:"))
async def deleted_mute(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    user_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    pool = await get_pool()

    until = moderation_queries.duration_to_datetime(10 * 60)
    await moderation_queries.set_mute(pool, user_id, until)

    await callback.answer(messages.MUTE_SUCCESS, show_alert=True)
    await _render_member_deleted(callback, user_id, page)


# ==================== استثناءات فردية لعضو (تم الإصلاح) ====================

@router.callback_query(F.data.startswith("owner:prot_exc:"))
async def show_member_exceptions(callback: CallbackQuery) -> None:
    """عرض استثناءات الحماية لعضو معين - مع إصلاح مشكلة العضو غير موجود"""
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
    
    # محاولة جلب العضو من قاعدة البيانات
    member = await members_queries.get_member(pool, user_id)
    
    if member is None:
        # إذا كان العضو غير موجود، نحاول إضافته
        logger.warning(f"العضو {user_id} غير موجود في قاعدة البيانات، محاولة إضافته...")
        
        try:
            # محاولة جلب معلومات العضو من المجموعة
            chat_member = await callback.bot.get_chat_member(
                chat_id=callback.message.chat.id, 
                user_id=user_id
            )
            user = chat_member.user
            
            # إضافة العضو إلى قاعدة البيانات
            await members_queries.add_or_update_member(
                pool, 
                user_id=user_id,
                username=user.username,
                full_name=user.full_name
            )
            
            # جلب العضو مرة أخرى
            member = await members_queries.get_member(pool, user_id)
            
            if member is None:
                await callback.answer("❌ لا يمكن إضافة العضو إلى قاعدة البيانات", show_alert=True)
                return
                
        except Exception as e:
            logger.error(f"فشل إضافة العضو {user_id}: {e}")
            await callback.answer("❌ العضو غير موجود في قاعدة البيانات ولا يمكن إضافته", show_alert=True)
            return

    # جلب الاستثناءات الحالية
    exceptions = await protection_queries.get_member_exceptions(pool, user_id)

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("owner:prot_exc_toggle:"))
async def toggle_member_exception(callback: CallbackQuery) -> None:
    """تبديل استثناء عضو لميزة معينة"""
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
    new_state = await protection_queries.toggle_member_exception(pool, user_id, feature_key)

    # جلب بيانات العضو للتأكيد
    member = await members_queries.get_member(pool, user_id)
    exceptions = await protection_queries.get_member_exceptions(pool, user_id)
    
    feature_label = protection_queries.FEATURE_LABELS.get(feature_key, feature_key)

    # رسالة تأكيد
    if new_state:
        confirm_msg = f"✅ تم استثناء {member['full_name']} من {feature_label}\nأصبح بإمكانه تجاوز الحظر العام."
    else:
        confirm_msg = f"❌ تم إلغاء استثناء {member['full_name']} من {feature_label}\nأصبح يخضع للإعدادات العامة."

    text = messages.member_exceptions_text(member["full_name"])
    keyboard = prot_keyboards.member_exceptions_keyboard(user_id, offset, exceptions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(confirm_msg, show_alert=False)


@router.callback_query(F.data == "owner:prot_exc_help")
async def show_exceptions_help(callback: CallbackQuery) -> None:
    """عرض مساعدة حول الاستثناءات"""
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

    # نحتاج لاستخراج user_id و offset من آخر رسالة
    # نستخدم طريقة بسيطة: زر رجوع للقائمة الرئيسية
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع للإعدادات", callback_data="owner:protection")],
            [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="owner:main")],
        ]
    )

    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()