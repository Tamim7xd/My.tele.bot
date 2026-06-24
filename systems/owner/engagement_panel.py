"""
لوحة التحكم - نظام التفاعل التلقائي المطور (engagement).
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.engagement import queries as engagement_queries
from systems.shop.queries import format_duration

router = Router(name="owner_engagement")

def _is_owner(uid: int | None) -> bool:
    return uid is not None and uid == OWNER_ID

def _main_keyboard(settings: dict) -> InlineKeyboardMarkup:
    status = "✅ مفعّل" if settings.get("enabled") else "❌ معطّل"
    interval_text = format_duration(settings.get("interval_seconds", 3600))

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{status} — تبديل التفعيل", callback_data="owner:eng_toggle")],
        [InlineKeyboardButton(text=f"⏱️ الفاصل: {interval_text}", callback_data="owner:eng_interval")],
        [InlineKeyboardButton(text="📝 سجل وقائمة الرسائل", callback_data="owner:eng_msg_list")],
        [InlineKeyboardButton(text="➕ إضافة رسالة جديدة", callback_data="owner:eng_add_prompt")],
        [InlineKeyboardButton(text="📜 تاريخ الإرسال الأخير", callback_data="owner:eng_history_view")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
    ])

@router.callback_query(F.data == "owner:engagement")
async def show_engagement(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    text = (
        f"🔔 <b>لوحة تحكم نظام التفاعل التلقائي الدوري</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✉️ عدد الرسائل المضافة بالسستم: {len(settings.get('messages', []))}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر الإجراء المطلوب ادناه:"
    )
    await callback.message.edit_text(text, reply_markup=_main_keyboard(settings))
    await callback.answer()

@router.callback_query(F.data == "owner:eng_toggle")
async def toggle_engagement(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    pool = await get_pool()
    new_state = await engagement_queries.toggle_engagement(pool)
    settings = await engagement_queries.get_engagement_settings(pool)
    await callback.message.edit_text(callback.message.text, reply_markup=_main_keyboard(settings))
    await callback.answer("✅ تم التفعيل" if new_state else "❌ تم التعطيل")

# --- قائمة وعرض وإدارة الرسائل المضافة ---

@router.callback_query(F.data == "owner:eng_msg_list")
async def show_msg_list(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    
    kb = []
    text = "📝 <b>قائمة الرسائل التلقائية المخزنة بالسستم:</b>\n\n"
    
    for m in settings.get("messages", []):
        act = "🟢" if m.get("active") else "🔴"
        btn = "🔘" if m.get("button_enabled") else "✖️"
        text += f"🆔 [{m['id']}] {act} زر: {btn} | {m['message_text'][:30]}...\n"
        kb.append([InlineKeyboardButton(text=f"إدارة الرسالة [{m['id']}]", callback_data=f"owner:eng_manage:{m['id']}")])
        
    kb.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:engagement")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("owner:eng_manage:"))
async def manage_message_screen(callback: CallbackQuery) -> None:
    mid = callback.data.split(":")[-1]
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    msg = next((x for x in settings["messages"] if x["id"] == mid), None)
    
    if not msg:
        await callback.answer("❌ الرسالة غير موجودة")
        return
        
    text = (
        f"⚙️ <b>إدارة الرسالة: [{mid}]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 <b>النص:</b> {msg['message_text']}\n"
        f"🔘 <b>نص الزر:</b> {msg['button_text']}\n"
        f"📊 <b>الحالة:</b> {'🟢 نشطة بالتدوير' if msg['active'] else '🔴 معطلة ومخفية'}\n"
        f"🔘 <b>حالة الزر السفلية:</b> {'✅ مفعّل ويظهر' if msg['button_enabled'] else '❌ معطّل ومخفي'}\n"
    )
    
    kb = [
        [InlineKeyboardButton(text="🔄 تبديل النشاط (ايقاف/تشغيل)", callback_data=f"owner:eng_switch_act:{mid}")],
        [InlineKeyboardButton(text="🔘 تبديل الزر (تعطيل/تفعيل)", callback_data=f"owner:eng_switch_btn:{mid}")],
        [InlineKeyboardButton(text="🗑️ حذف هذه الرسالة", callback_data=f"owner:eng_delete_msg:{mid}")],
        [InlineKeyboardButton(text="🔙 رجوع للقائمة", callback_data="owner:eng_msg_list")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("owner:eng_switch_act:"))
async def switch_action(callback: CallbackQuery) -> None:
    mid = callback.data.split(":")[-1]
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    for x in settings["messages"]:
        if x["id"] == mid:
            x["active"] = not x["active"]
    await engagement_queries.set_engagement_settings(pool, settings)
    await callback.answer("✅ تم تعديل النشاط")
    await show_msg_list(callback)

@router.callback_query(F.data.startswith("owner:eng_switch_btn:"))
async def switch_button(callback: CallbackQuery) -> None:
    mid = callback.data.split(":")[-1]
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    for x in settings["messages"]:
        if x["id"] == mid:
            x["button_enabled"] = not x["button_enabled"]
    await engagement_queries.set_engagement_settings(pool, settings)
    await callback.answer("✅ تم تعديل حالة الزر")
    await show_msg_list(callback)

@router.callback_query(F.data.startswith("owner:eng_delete_msg:"))
async def delete_action(callback: CallbackQuery) -> None:
    mid = callback.data.split(":")[-1]
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["messages"] = [x for x in settings["messages"] if x["id"] != mid]
    await engagement_queries.set_engagement_settings(pool, settings)
    await callback.answer("🗑️ تم الحذف بنجاح")
    await show_msg_list(callback)

# --- إضافة رسالة جديدة بسياق الـ FSM وحالات السستم الأصلي ---

@router.callback_query(F.data == "owner:eng_add_prompt")
async def add_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    await state.set_state(OwnerStates.waiting_engagement_message)
    await callback.message.edit_text("✏️ أرسل الآن نص الرسالة التلقائية الجديدة التي تريد إضافتها:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:engagement")]]))
    await callback.answer()

@router.message(OwnerStates.waiting_engagement_message)
async def process_text_in(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text: return
    await state.update_data(msg_text=message.text)
    await state.set_state(OwnerStates.waiting_engagement_button)
    await message.reply("✏️ ممتاز، الآن أرسل اسم الزر الشفاف التابع لها (مثال: 📋 قائمتي):")

@router.message(OwnerStates.waiting_engagement_button)
async def process_btn_in(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text: return
    data = await state.get_data()
    pool = await get_pool()
    
    await engagement_queries.add_new_message(pool, data["msg_text"], message.text)
    await state.clear()
    
    settings = await engagement_queries.get_engagement_settings(pool)
    await message.reply("✅ تم إضافة الرسالة الجديدة بنجاح إلى قاعدة بيانات التدوير الدوري!", reply_markup=_main_keyboard(settings))

# --- عرض تاريخ سجل الإرسال ---

@router.callback_query(F.data == "owner:eng_history_view")
async def view_history(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    
    history_logs = settings.get("history", [])
    if not history_logs:
        text = "📜 <b>تاريخ الإرسال فارغ حالياً، لم يتم إرسال أي رسائل تدويرية بعد.</b>"
    else:
        text = "📜 <b>آخر عمليات إرسال النظام للمجموعة:</b>\n\n" + "\n".join(history_logs)
        
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:engagement")]]))

# --- تعديل مؤقت السستم الأصلي دون تغيير الكود الفرعي ---

@router.callback_query(F.data == "owner:eng_interval")
async def interval_prompt(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    
    kb = [
        [InlineKeyboardButton(text="30 ثانية", callback_data="owner:eng_set_interval:30"),
         InlineKeyboardButton(text="دقيقة", callback_data="owner:eng_set_interval:60")],
        [InlineKeyboardButton(text="ساعة", callback_data="owner:eng_set_interval:3600"),
         InlineKeyboardButton(text="🔢 مخصص", callback_data="owner:eng_set_interval:custom")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:engagement")]
    ]
    await callback.message.edit_text("⏱️ اختر الفاصل الزمني للتفاعل الدوري:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("owner:eng_set_interval:"))
async def set_interval(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id): return
    value = callback.data.split(":")[-1]

    if value == "custom":
        await state.set_state(OwnerStates.waiting_engagement_interval)
        await callback.message.edit_text("✏️ أرسل الفاصل الزمني بالثواني:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:engagement")]]))
        return

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["interval_seconds"] = int(value)
    await engagement_queries.set_engagement_settings(pool, settings)
    await show_engagement(callback, state)

@router.message(OwnerStates.waiting_engagement_interval)
async def custom_interval_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text or not message.text.isdigit(): return
    val = int(message.text)
    if val < 30: return
    
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["interval_seconds"] = val
    await engagement_queries.set_engagement_settings(pool, settings)
    await state.clear()
    await message.reply(f"✅ تم تحديث الفاصل إلى {format_duration(val)}", reply_markup=_main_keyboard(settings))
