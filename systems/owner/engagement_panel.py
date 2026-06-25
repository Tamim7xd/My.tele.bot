"""
لوحة التحكم - نظام التفاعل التلقائي (engagement) - النسخة المتطورة.
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


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:engagement")]]
    )


def _main_keyboard(settings: dict) -> InlineKeyboardMarkup:
    status = "✅ مفعّل" if settings.get("enabled") else "❌ معطّل"
    interval_text = format_duration(settings.get("interval_seconds", 3600))
    disable_cmds = "✅ موقوفة" if settings.get("disable_group_commands") else "❌ تعمل"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{status} — تبديل التفعيل", callback_data="owner:eng_toggle")],
            [InlineKeyboardButton(text=f"⏱️ الفاصل الزمني: {interval_text}", callback_data="owner:eng_interval")],
            [InlineKeyboardButton(text="✏️ نص الرسالة", callback_data="owner:eng_message")],
            [InlineKeyboardButton(text="🔘 نص الزر", callback_data="owner:eng_button")],
            [InlineKeyboardButton(text="🎛️ الأزرار الاختيارية", callback_data="owner:eng_buttons")],
            [InlineKeyboardButton(text=f"🚫 أوامر المجموعة: {disable_cmds}", callback_data="owner:eng_toggle_cmds")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")],
        ]
    )


def _buttons_keyboard(settings: dict) -> InlineKeyboardMarkup:
    from systems.engagement.queries import BUTTON_LABELS

    buttons = []
    for key, label in BUTTON_LABELS.items():
        icon = "✅" if settings.get(key, True) else "❌"
        buttons.append([
            InlineKeyboardButton(text=f"{icon} {label}", callback_data=f"owner:eng_toggle_btn:{key}")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:engagement")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _interval_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 ثانية", callback_data="owner:eng_set_interval:30"),
                InlineKeyboardButton(text="دقيقة", callback_data="owner:eng_set_interval:60"),
                InlineKeyboardButton(text="5 دقائق", callback_data="owner:eng_set_interval:300"),
            ],
            [
                InlineKeyboardButton(text="30 دقيقة", callback_data="owner:eng_set_interval:1800"),
                InlineKeyboardButton(text="ساعة", callback_data="owner:eng_set_interval:3600"),
                InlineKeyboardButton(text="6 ساعات", callback_data="owner:eng_set_interval:21600"),
            ],
            [InlineKeyboardButton(text="🔢 مخصص (ثواني)", callback_data="owner:eng_set_interval:custom")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:engagement")],
        ]
    )


async def _refresh_main(callback: CallbackQuery) -> None:
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    text = (
        f"🔔 <b>التفاعل التلقائي</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 الرسالة: {settings.get('message_text', '')}\n"
        f"🔘 الزر: {settings.get('button_text', '')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"اختر ما تريد تعديله:"
    )

    await callback.message.edit_text(text, reply_markup=_main_keyboard(settings))


@router.callback_query(F.data == "owner:engagement")
async def show_engagement(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await _refresh_main(callback)
    await callback.answer()


@router.callback_query(F.data == "owner:eng_toggle")
async def toggle_engagement(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    new_state = await engagement_queries.toggle_engagement(pool)
    await _refresh_main(callback)
    await callback.answer("✅ تم التفعيل" if new_state else "❌ تم التعطيل")


@router.callback_query(F.data == "owner:eng_toggle_cmds")
async def toggle_disable_commands(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    new_state = await engagement_queries.toggle_disable_commands(pool)
    await _refresh_main(callback)

    status = "✅ تم إيقاف الأوامر النصية" if new_state else "❌ تم إعادة تفعيل الأوامر النصية"
    await callback.answer(status, show_alert=True)


@router.callback_query(F.data == "owner:eng_buttons")
async def show_buttons_settings(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)

    await callback.message.edit_text(
        "🎛️ <b>الأزرار الاختيارية</b>\n━━━━━━━━━━━━━━━\nاضغط لتفعيل/تعطيل كل زر:",
        reply_markup=_buttons_keyboard(settings),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("owner:eng_toggle_btn:"))
async def toggle_button(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    btn_key = callback.data.split(":")[-1]

    pool = await get_pool()
    new_state = await engagement_queries.toggle_button(pool, btn_key)
    settings = await engagement_queries.get_engagement_settings(pool)

    await callback.message.edit_text(
        "🎛️ <b>الأزرار الاختيارية</b>\n━━━━━━━━━━━━━━━\nاضغط لتفعيل/تعطيل كل زر:",
        reply_markup=_buttons_keyboard(settings),
    )
    await callback.answer("✅" if new_state else "❌")


@router.callback_query(F.data == "owner:eng_interval")
async def interval_prompt(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text("⏱️ اختر الفاصل الزمني:", reply_markup=_interval_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("owner:eng_set_interval:"))
async def set_interval(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    value = callback.data.split(":")[-1]

    if value == "custom":
        await state.set_state(OwnerStates.waiting_engagement_interval)
        await callback.message.edit_text("✏️ أرسل الفاصل الزمني بالثواني:", reply_markup=_cancel_kb())
        await callback.answer()
        return

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["interval_seconds"] = int(value)
    await engagement_queries.set_engagement_settings(pool, settings)

    await _refresh_main(callback)
    await callback.answer(f"✅ تم تحديث الفاصل إلى {format_duration(int(value))}")


@router.message(OwnerStates.waiting_engagement_interval)
async def custom_interval_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    if not message.text or not message.text.isdigit() or int(message.text) < 30:
        await message.reply("❌ الحد الأدنى 30 ثانية.", reply_markup=_cancel_kb())
        return

    value = int(message.text)
    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["interval_seconds"] = value
    await engagement_queries.set_engagement_settings(pool, settings)
    await state.clear()

    await message.reply(
        f"✅ تم تحديث الفاصل إلى {format_duration(value)}",
        reply_markup=_main_keyboard(settings),
    )


@router.callback_query(F.data == "owner:eng_message")
async def message_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_engagement_message)
    await callback.message.edit_text("✏️ أرسل نص الرسالة الدورية:", reply_markup=_cancel_kb())
    await callback.answer()


@router.message(OwnerStates.waiting_engagement_message)
async def message_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["message_text"] = message.text
    await engagement_queries.set_engagement_settings(pool, settings)
    await state.clear()

    await message.reply("✅ تم تحديث نص الرسالة.", reply_markup=_main_keyboard(settings))


@router.callback_query(F.data == "owner:eng_button")
async def button_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_engagement_button)
    await callback.message.edit_text("✏️ أرسل نص زر القائمة:", reply_markup=_cancel_kb())
    await callback.answer()


@router.message(OwnerStates.waiting_engagement_button)
async def button_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return

    pool = await get_pool()
    settings = await engagement_queries.get_engagement_settings(pool)
    settings["button_text"] = message.text
    await engagement_queries.set_engagement_settings(pool, settings)
    await state.clear()

    await message.reply("✅ تم تحديث نص الزر.", reply_markup=_main_keyboard(settings))
