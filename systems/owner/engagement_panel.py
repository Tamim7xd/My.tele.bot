from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from core.db import get_pool
from systems.engagement import queries as engagement_queries
from systems.owner.keyboards import get_engagement_main_kb, get_messages_list_kb, get_message_manage_kb
from systems.owner.states import EngagementStates # أضف الأنواع المطلوبة في ملف التخرين الخاص بك

router = Router()

@router.callback_query(F.data == "owner:engagement_panel")
async def show_panel(callback: CallbackQuery):
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    text = (
        "📊 **لوحة تحكم نظام التفاعل التلقائي**\n\n"
        f"الحالة الحالية: {'🟢 مفعّل' if settings.get('enabled') else '🔴 معطّل'}\n"
        f"الفاصل الزمني: {settings.get('interval_seconds', 3600) // 60} دقيقة\n"
    )
    await callback.message.edit_text(text, reply_markup=get_engagement_main_kb(settings))

@router.callback_query(F.data == "owner:eng_msg_registry")
async def show_registry(callback: CallbackQuery):
    pool = await get_pool()
    messages = await engagement_queries.get_all_messages(pool)
    await callback.message.edit_text(
        "🗂️ **سجل الرسائل التلقائية المستهدفة:**\nإضغط على أي رسالة لإدارتها، تعديلها، أو حذفها.",
        reply_markup=get_messages_list_kb(messages)
    )

@router.callback_query(F.data.startswith("owner:manage_msg:"))
async def manage_single_message(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[2])
    pool = await get_pool()
    msg = await engagement_queries.get_message_by_id(pool, msg_id)
    
    if not msg:
        await callback.answer("❌ هذه الرسالة لم تعد موجودة.")
        return

    status = "🟢 نشطة (يتم إرسالها دورياً)" if msg["is_active"] else "⚫ موقوفة مؤقتاً"
    text = f"📝 **إدارة الرسالة رقم #{msg['id']}**\n\n**الحالة:** {status}\n\n**النص الحالي:**\n`{msg['text']}`"
    
    await callback.message.edit_text(text, reply_markup=get_message_manage_kb(msg_id, msg["is_active"]))

@router.callback_query(F.data.startswith("owner:toggle_msg:"))
async def toggle_msg(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[2])
    pool = await get_pool()
    new_state = await engagement_queries.toggle_message_status(pool, msg_id)
    await callback.answer("🟢 تم تفعيل الرسالة" if new_state else "🔴 تم إيقاف الرسالة مؤقتاً")
    await manage_single_message(callback)

@router.callback_query(F.data.startswith("owner:delete_msg:"))
async def delete_msg(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[2])
    pool = await get_pool()
    await engagement_queries.delete_message(pool, msg_id)
    await callback.answer("🗑️ تم حذف الرسالة بنجاح من السجل")
    await show_registry(callback)
