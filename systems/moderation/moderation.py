"""
نظام الحظر/الكتم/التحذير - الملف الرئيسي.

التدفق:

1. رد على عضو + كتابة "كتم" (يحتاج صلاحية mute)
   أو "حظر" (يحتاج صلاحية ban)
   أو "تحذير" (يحتاج صلاحية warn)
        ↓
2. كتم/حظر: فئة المدة (ثواني/دقائق/ساعات/أيام) -> مدة محددة -> تأكيد (+ مخالفة)
   تحذير: تأكيد مباشرة
        ↓
3. عند التأكيد:
   - تطبيق الكتم/الحظر/التحذير في قاعدة البيانات
   - إشعار للمجموعة
   - تسجيل في الأرشيف (وفي المخالفات إن طُلب)

⚠️ فحص التسلسل الهرمي (can_act_on): نفس آلية rewards.

ملاحظة عن الكتم/الحظر الفعلي في تيليجرام:
هذا الملف يسجل الحالة في قاعدة البيانات (للعرض في "حساب" واللوحة)
ويحاول أيضاً تطبيق restrict_chat_member / ban_chat_member الفعلي
عبر Bot API. إذا فشل (مثلاً البوت ليس أدمن)، يستمر العمل
بالاعتماد على قاعدة البيانات فقط دون إيقاف التدفق.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ChatPermissions

from core.database import get_pool
from systems.members import queries as members_queries
from systems.moderators import permissions
from systems.moderation import keyboards, queries as moderation_queries
from systems.moderation.states import ModerationStates
from systems.moderation.notifications import messages


router = Router(name="moderation")


MUTE_COMMANDS = {"كتم"}
BAN_COMMANDS = {"حظر"}
WARN_COMMANDS = {"تحذير"}


# ===== خطوة 1: استقبال الأمر بالرد =====

@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(MUTE_COMMANDS),
)
async def start_mute(message: Message, state: FSMContext) -> None:
    await _start_duration_flow(message, state, action="mute")


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(BAN_COMMANDS),
)
async def start_ban(message: Message, state: FSMContext) -> None:
    await _start_duration_flow(message, state, action="ban")


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(WARN_COMMANDS),
)
async def start_warn(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply(messages.NO_REPLY)
        return

    pool = await get_pool()

    if not await permissions.has_permission(pool, message.from_user.id, "warn"):
        await message.reply(messages.NO_PERMISSION)
        return

    target = message.reply_to_message.from_user

    await members_queries.ensure_member_exists(
        pool,
        user_id=target.id,
        username=target.username,
        full_name=target.full_name,
    )

    if not await permissions.can_act_on(pool, message.from_user.id, target.id):
        await message.reply(messages.NO_PERMISSION)
        return

    replied_text = message.reply_to_message.text or message.reply_to_message.caption

    await state.update_data(
        action="warn",
        target_user_id=target.id,
        target_username=target.username,
        target_full_name=target.full_name,
        replied_text=replied_text,
        actor_full_name=message.from_user.full_name,
    )
    await state.set_state(ModerationStates.in_progress)

    text = messages.confirm_warn_text(replied_text)
    keyboard = keyboards.warn_confirm_keyboard()

    await message.reply(text, reply_markup=keyboard)


async def _start_duration_flow(message: Message, state: FSMContext, action: str) -> None:
    """منطق مشترك لبدء تدفق الكتم/الحظر (يحتاج اختيار مدة)."""
    if message.from_user is None:
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply(messages.NO_REPLY)
        return

    pool = await get_pool()

    required_permission = "mute" if action == "mute" else "ban"

    if not await permissions.has_permission(pool, message.from_user.id, required_permission):
        await message.reply(messages.NO_PERMISSION)
        return

    target = message.reply_to_message.from_user

    await members_queries.ensure_member_exists(
        pool,
        user_id=target.id,
        username=target.username,
        full_name=target.full_name,
    )

    if not await permissions.can_act_on(pool, message.from_user.id, target.id):
        await message.reply(messages.NO_PERMISSION)
        return

    replied_text = message.reply_to_message.text or message.reply_to_message.caption

    await state.update_data(
        action=action,
        target_user_id=target.id,
        target_username=target.username,
        target_full_name=target.full_name,
        target_chat_id=message.chat.id,
        replied_text=replied_text,
        actor_full_name=message.from_user.full_name,
    )
    await state.set_state(ModerationStates.in_progress)

    action_label = "كتم" if action == "mute" else "حظر"

    text = messages.category_selection_text(action_label, replied_text)
    keyboard = keyboards.category_keyboard(action)

    await message.reply(text, reply_markup=keyboard)


# ===== خطوة 2: اختيار فئة المدة =====

@router.callback_query(F.data.startswith("moderation:cat:"))
async def select_category(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, _, action, category = callback.data.split(":")

    await state.update_data(category=category)

    action_label = "كتم" if action == "mute" else "حظر"

    text = messages.duration_selection_text(action_label)
    keyboard = keyboards.duration_keyboard(action, category)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("moderation:cat_back:"))
async def category_back(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    action = callback.data.split(":")[-1]

    data = await state.get_data()
    replied_text = data.get("replied_text")

    action_label = "كتم" if action == "mute" else "حظر"

    text = messages.category_selection_text(action_label, replied_text)
    keyboard = keyboards.category_keyboard(action)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== خطوة 3: اختيار المدة المحددة =====

@router.callback_query(F.data.startswith("moderation:dur:"))
async def select_duration(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, _, action, seconds_str = callback.data.split(":")
    seconds = int(seconds_str)

    await state.update_data(duration_seconds=seconds)

    action_label = "كتم" if action == "mute" else "حظر"
    duration_text = messages.duration_label(seconds)

    text = messages.confirm_text(action_label, duration_text)
    keyboard = keyboards.confirm_keyboard(action, with_violation=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== خطوة 4: التأكيد =====

@router.callback_query(
    F.data.startswith("moderation:confirm:") | F.data.startswith("moderation:confirm_violation:")
)
async def confirm_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None or callback.from_user is None:
        return

    with_violation = callback.data.startswith("moderation:confirm_violation:")
    action = callback.data.split(":")[-1]

    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    target_username = data.get("target_username")
    target_full_name = data.get("target_full_name")
    target_chat_id = data.get("target_chat_id")
    replied_text = data.get("replied_text")
    duration_seconds = data.get("duration_seconds")

    if target_user_id is None or target_full_name is None:
        await state.clear()
        await callback.answer()
        return

    pool = await get_pool()

    if action == "warn":
        await moderation_queries.log_archive_entry(
            pool,
            user_id=target_user_id,
            action_type="warn",
            reason=None,
            replied_message=replied_text,
            done_by=callback.from_user.id,
        )

        notification_text = messages.warn_notification(
            full_name=target_full_name,
            username=target_username,
            reason=None,
            by_full_name=callback.from_user.full_name,
        )

        await callback.message.edit_text(notification_text)
        await state.clear()
        await callback.answer()
        return

    if duration_seconds is None:
        await state.clear()
        await callback.answer()
        return

    until = moderation_queries.duration_to_datetime(duration_seconds)
    duration_text = messages.duration_label(duration_seconds)

    if action == "mute":
        await moderation_queries.set_mute(pool, target_user_id, until)

        if target_chat_id:
            try:
                await callback.bot.restrict_chat_member(
                    chat_id=target_chat_id,
                    user_id=target_user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
            except Exception:
                pass

        await moderation_queries.log_archive_entry(
            pool,
            user_id=target_user_id,
            action_type="mute",
            reason=None,
            replied_message=replied_text,
            done_by=callback.from_user.id,
        )

        if with_violation:
            await moderation_queries.log_archive_entry(
                pool,
                user_id=target_user_id,
                action_type="violation",
                reason=None,
                replied_message=replied_text,
                done_by=callback.from_user.id,
            )

        notification_text = messages.mute_notification(
            full_name=target_full_name,
            username=target_username,
            duration_text=duration_text,
            reason=None,
            by_full_name=callback.from_user.full_name,
        )

    else:  # ban
        await moderation_queries.set_ban(pool, target_user_id, until)

        if target_chat_id:
            try:
                await callback.bot.ban_chat_member(
                    chat_id=target_chat_id,
                    user_id=target_user_id,
                    until_date=until,
                )
            except Exception:
                pass

        await moderation_queries.log_archive_entry(
            pool,
            user_id=target_user_id,
            action_type="ban",
            reason=None,
            replied_message=replied_text,
            done_by=callback.from_user.id,
        )

        if with_violation:
            await moderation_queries.log_archive_entry(
                pool,
                user_id=target_user_id,
                action_type="violation",
                reason=None,
                replied_message=replied_text,
                done_by=callback.from_user.id,
            )

        notification_text = messages.ban_notification(
            full_name=target_full_name,
            username=target_username,
            duration_text=duration_text,
            reason=None,
            by_full_name=callback.from_user.full_name,
        )

    await callback.message.edit_text(notification_text)
    await state.clear()
    await callback.answer()


# ===== الإلغاء =====

@router.callback_query(F.data.startswith("moderation:cancel:"))
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await state.clear()
    await callback.message.edit_text(messages.CANCELLED)
    await callback.answer()
