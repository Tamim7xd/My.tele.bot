"""
نظام التحويل (transfer).

الأوامر: "تحويل" أو "إرسال" + الرد على رسالة عضو + المبلغ في نفس الرسالة
مثال: "تحويل 1.000" (مع الرد على رسالة العضو)

التدفق:
1. عضو يكتب "تحويل 5.000" رداً على رسالة عضو آخر
2. البوت يتحقق: رد صحيح + مبلغ صحيح + رصيد كافٍ + حدود التحويل
3. يعرض رسالة تأكيد بالتفاصيل (المبلغ + الرسوم إن وُجدت + المبلغ النهائي)
4. يضغط "✅ تأكيد" → يُنفَّذ التحويل + إشعار للطرفين
   أو "❌ إلغاء" → تُلغى العملية
"""

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.database import get_pool
from systems.members import queries as members_queries
from systems.wallet import wallet
from systems.transfer import queries as transfer_queries
from systems.transfer.notifications import messages


router = Router(name="transfer")

TRIGGER_WORDS = {"تحويل", "إرسال", "ارسال"}


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def handle_transfer(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    text = message.text.strip()

    # التحقق من أن الرسالة تبدأ بكلمة تحويل/إرسال
    matched_trigger = None
    for trigger in TRIGGER_WORDS:
        if text == trigger or text.lower().startswith(trigger + " "):
            matched_trigger = trigger
            break

    if matched_trigger is None:
        raise SkipHandler

    # التحقق من وجود رد على رسالة
    if message.reply_to_message is None or message.reply_to_message.from_user is None:
        await message.reply(messages.NO_REPLY)
        return

    target_user = message.reply_to_message.from_user

    # منع التحويل لنفسه
    if target_user.id == message.from_user.id:
        await message.reply(messages.SELF_TRANSFER)
        return

    # استخراج المبلغ من النص
    amount_text = text[len(matched_trigger):].strip()
    amount = transfer_queries.parse_transfer_amount(amount_text)

    if amount is None:
        await message.reply(messages.INVALID_AMOUNT)
        return

    pool = await get_pool()

    # التحقق من وجود المُستلِم في النظام
    target_member = await members_queries.get_member(pool, target_user.id)
    if target_member is None:
        await message.reply(messages.TARGET_NOT_FOUND)
        return

    # التحقق من الحدود الدنيا والقصوى
    min_amount = await transfer_queries.get_min_transfer(pool)
    max_amount = await transfer_queries.get_max_transfer(pool)

    if amount < min_amount:
        await message.reply(messages.BELOW_MIN.format(min=min_amount))
        return

    if max_amount > 0 and amount > max_amount:
        await message.reply(messages.ABOVE_MAX.format(max=max_amount))
        return

    # حساب الرسوم
    fee_percent = await transfer_queries.get_fee_percent(pool)
    fee_amount = int(amount * fee_percent / 100)
    final_amount = amount - fee_amount

    # التحقق من كفاية الرصيد
    sender_balance = await wallet.get_balance(pool, message.from_user.id)
    if sender_balance < amount:
        await message.reply(messages.INSUFFICIENT_BALANCE)
        return

    # عرض رسالة تأكيد
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ تأكيد",
                    callback_data=f"transfer:confirm:{message.from_user.id}:{target_user.id}:{amount}:{final_amount}",
                ),
                InlineKeyboardButton(
                    text="❌ إلغاء",
                    callback_data=f"transfer:cancel:{message.from_user.id}",
                ),
            ]
        ]
    )

    await message.reply(
        messages.confirm_text(target_member["full_name"], amount, fee_percent, final_amount),
        reply_markup=confirm_keyboard,
    )


@router.callback_query(F.data.startswith("transfer:confirm:"))
async def confirm_transfer(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    sender_id = int(parts[2])
    target_id = int(parts[3])
    amount = int(parts[4])
    final_amount = int(parts[5])

    # فقط المُرسِل يمكنه التأكيد
    if callback.from_user.id != sender_id:
        await callback.answer()
        return

    pool = await get_pool()

    # إعادة التحقق من الرصيد لحظة التنفيذ (ضمان عدم تغيّره بين الطلب والتأكيد)
    sender_balance = await wallet.get_balance(pool, sender_id)
    if sender_balance < amount:
        await callback.message.edit_text(messages.INSUFFICIENT_BALANCE)
        await callback.answer()
        return

    # تنفيذ التحويل
    await wallet.deduct_balance(pool, sender_id, amount)
    await wallet.add_balance(pool, target_id, final_amount)

    # الأرصدة الجديدة
    new_sender_balance = await wallet.get_balance(pool, sender_id)
    new_target_balance = await wallet.get_balance(pool, target_id)

    # بيانات المُستلِم للإشعار
    target_member = await members_queries.get_member(pool, target_id)
    sender_member = await members_queries.get_member(pool, sender_id)

    if target_member is None or sender_member is None:
        await callback.answer()
        return

    # تعديل رسالة التأكيد لتصبح رسالة نجاح
    await callback.message.edit_text(
        messages.success_text(target_member["full_name"], final_amount, new_sender_balance)
    )

    # إشعار المُستلِم في المجموعة (رد على الرسالة الأصلية أو رسالة مستقلة)
    try:
        await callback.message.answer(
            messages.received_text(sender_member["full_name"], final_amount, new_target_balance)
        )
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("transfer:cancel:"))
async def cancel_transfer(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    sender_id = int(callback.data.split(":")[-1])

    if callback.from_user.id != sender_id:
        await callback.answer()
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer("❌ تم إلغاء التحويل")

