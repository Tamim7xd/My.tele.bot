"""
نظام الخصم والمكافأة - الملف الرئيسي.

التدفق الكامل:

1. رد على عضو + كتابة "خصم" (يحتاج صلاحية deduct)
   أو "مكافأة"/"مكافاة"/"مكافئة" (يحتاج صلاحية reward)
        ↓
2. تظهر أزرار اختيار المبلغ (1,000 / 2,500 / 5,000 / 10,000) + إلغاء
        ↓
3. عند اختيار مبلغ -> تُحفظ بيانات العملية في FSM context،
   وتظهر رسالة طلب السبب + زر "بدون سبب" + إلغاء
        ↓
4. المشرف يكتب السبب نصاً، أو يضغط "بدون سبب"
        ↓
5. تظهر أزرار التأكيد:
   - ✅ تأكيد
   - ⚠️ تأكيد + مخالفة (فقط للخصم)
   - ❌ إلغاء
        ↓
6. عند التأكيد:
   - تعديل الرصيد عبر wallet.py
   - إشعار للمجموعة
   - تسجيل في الأرشيف (وفي المخالفات إن طُلب)

هذا الملف مستقل - يستخدم:
- systems/wallet/wallet.py (تعديل الرصيد)
- systems/moderators/permissions.py (التحقق من الصلاحيات)
- systems/members/queries.py (جلب بيانات الأعضاء)
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.database import get_pool
from systems.members import queries as members_queries
from systems.moderators import permissions
from systems.wallet import wallet
from systems.rewards import keyboards, queries as rewards_queries
from systems.rewards.states import RewardStates
from systems.rewards.notifications import messages


router = Router(name="rewards")


DEDUCT_COMMANDS = {"خصم"}
REWARD_COMMANDS = {"مكافأة", "مكافاة", "مكافئة"}


# ===== خطوة 1: استقبال أمر "خصم" أو "مكافأة" بالرد =====

@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(DEDUCT_COMMANDS),
)
async def start_deduct(message: Message, state: FSMContext) -> None:
    await _start_flow(message, state, action="deduct")


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.in_(REWARD_COMMANDS),
)
async def start_reward(message: Message, state: FSMContext) -> None:
    await _start_flow(message, state, action="reward")


async def _start_flow(message: Message, state: FSMContext, action: str) -> None:
    """
    منطق مشترك لبدء تدفق الخصم/المكافأة.
    action: "deduct" أو "reward"
    """
    if message.from_user is None:
        return

    pool = await get_pool()

    required_permission = "deduct" if action == "deduct" else "reward"

    if not await permissions.has_permission(pool, message.from_user.id, required_permission):
        # صمت تام - لا رد للعضو الذي لا يملك الصلاحية
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply(messages.NO_REPLY)
        return

    target = message.reply_to_message.from_user

    # تسجيل الهدف احتياطياً إن لم يكن مسجلاً
    await members_queries.ensure_member_exists(
        pool,
        user_id=target.id,
        username=target.username,
        full_name=target.full_name,
    )

    # فحص التسلسل الهرمي: لا يمكن للضعيف التصرف على الأقوى أو المساوي
    if not await permissions.can_act_on(pool, message.from_user.id, target.id):
        # صمت تام - لا رد للعضو الذي لا يملك الصلاحية
        return

    # حفظ بيانات العملية في FSM context
    await state.update_data(
        action=action,
        target_user_id=target.id,
        target_username=target.username,
        target_full_name=target.full_name,
        replied_text=message.reply_to_message.text or message.reply_to_message.caption,
        actor_full_name=message.from_user.full_name,
    )

    action_label = "خصم" if action == "deduct" else "مكافأة"
    replied_text = message.reply_to_message.text or message.reply_to_message.caption

    text = messages.amount_selection_text(action_label, replied_text)
    keyboard = await keyboards.amount_keyboard(pool, action)

    await message.reply(text, reply_markup=keyboard)


# ===== خطوة 2: اختيار المبلغ =====

@router.callback_query(F.data.startswith("rewards:amount:"))
async def select_amount(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, _, action, amount_str = callback.data.split(":")
    amount = int(amount_str)

    await state.update_data(amount=amount)
    await state.set_state(RewardStates.waiting_reason)

    action_label = "خصم" if action == "deduct" else "مكافأة"

    text = messages.ask_reason_text(action_label, amount)
    keyboard = keyboards.skip_reason_keyboard(action)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== خطوة 3أ: كتابة السبب نصاً =====

@router.message(RewardStates.waiting_reason)
async def receive_reason(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        return

    data = await state.get_data()
    action = data.get("action")
    amount = data.get("amount")

    if action is None or amount is None:
        await state.clear()
        return

    await state.update_data(reason=message.text)

    action_label = "خصم" if action == "deduct" else "مكافأة"

    text = messages.confirm_text(action_label, amount, message.text)
    keyboard = keyboards.confirm_keyboard(action)

    await message.reply(text, reply_markup=keyboard)


# ===== خطوة 3ب: ضغط "بدون سبب" =====

@router.callback_query(F.data.startswith("rewards:skip_reason:"))
async def skip_reason(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, _, action = callback.data.split(":")

    data = await state.get_data()
    amount = data.get("amount")

    if amount is None:
        await state.clear()
        await callback.answer()
        return

    await state.update_data(reason=None)

    action_label = "خصم" if action == "deduct" else "مكافأة"

    text = messages.confirm_text(action_label, amount, None)
    keyboard = keyboards.confirm_keyboard(action)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ===== خطوة 4: التأكيد =====

@router.callback_query(F.data.startswith("rewards:confirm:") | F.data.startswith("rewards:confirm_violation:"))
async def confirm_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or callback.message is None or callback.from_user is None:
        return

    with_violation = callback.data.startswith("rewards:confirm_violation:")
    action = callback.data.split(":")[-1]

    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    target_username = data.get("target_username")
    target_full_name = data.get("target_full_name")
    replied_text = data.get("replied_text")
    amount = data.get("amount")
    reason = data.get("reason")

    if target_user_id is None or amount is None or target_full_name is None:
        await state.clear()
        await callback.answer()
        return

    pool = await get_pool()

    if action == "deduct":
        success = await wallet.deduct_balance(pool, target_user_id, amount)

        if not success:
            await callback.message.edit_text(messages.INSUFFICIENT_BALANCE_FOR_DEDUCT)
            await state.clear()
            await callback.answer()
            return

        await rewards_queries.log_archive_entry(
            pool,
            user_id=target_user_id,
            action_type="deduct",
            amount=amount,
            reason=reason,
            replied_message=replied_text,
            done_by=callback.from_user.id,
        )

        if with_violation:
            await rewards_queries.log_archive_entry(
                pool,
                user_id=target_user_id,
                action_type="violation",
                amount=None,
                reason=reason,
                replied_message=replied_text,
                done_by=callback.from_user.id,
            )

        notification_text = messages.deduct_notification(
            full_name=target_full_name,
            username=target_username,
            amount=amount,
            reason=reason,
            by_full_name=callback.from_user.full_name,
        )

    else:  # reward
        await wallet.add_balance(pool, target_user_id, amount)

        await rewards_queries.log_archive_entry(
            pool,
            user_id=target_user_id,
            action_type="reward",
            amount=amount,
            reason=reason,
            replied_message=replied_text,
            done_by=callback.from_user.id,
        )

        notification_text = messages.reward_notification(
            full_name=target_full_name,
            username=target_username,
            amount=amount,
            reason=reason,
            by_full_name=callback.from_user.full_name,
        )

    await callback.message.edit_text(notification_text)
    await state.clear()
    await callback.answer()


# ===== الإلغاء =====

@router.callback_query(F.data.startswith("rewards:cancel:"))
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await state.clear()
    await callback.message.edit_text(messages.CANCELLED)
    await callback.answer()
