"""
لوحة التحكم - نظام الإعلانات المتطور.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import get_pool
from core.config import OWNER_ID
from systems.owner.states import OwnerStates
from systems.announcements import queries as ann_queries


router = Router(name="owner_announcements")


def _is_owner(uid: int | None) -> bool:
    return uid is not None and uid == OWNER_ID


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")]]
    )


def _skip_kb(cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ تخطي", callback_data=cb)],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


def _ann_list_kb(announcements: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for i, ann in enumerate(announcements):
        trigger = ann.get("trigger", "؟")
        icons = ""
        if ann.get("file_id"):
            icons += "📎"
        if ann.get("pin"):
            icons += "📌"
        if ann.get("button_url"):
            icons += "🔘"
        buttons.append([
            InlineKeyboardButton(text=f"{icons} {trigger}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:ann_delete:{i}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ إضافة إعلان", callback_data="owner:ann_add_trigger")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _media_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🖼️ صورة", callback_data="owner:ann_media:photo"),
                InlineKeyboardButton(text="🎥 فيديو", callback_data="owner:ann_media:video"),
            ],
            [
                InlineKeyboardButton(text="🎞️ GIF", callback_data="owner:ann_media:animation"),
                InlineKeyboardButton(text="🎭 ملصق", callback_data="owner:ann_media:sticker"),
            ],
            [InlineKeyboardButton(text="⏭️ بدون وسائط", callback_data="owner:ann_media:none")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


def _pin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📌 تثبيت", callback_data="owner:ann_pin:yes"),
                InlineKeyboardButton(text="🚫 بدون تثبيت", callback_data="owner:ann_pin:no"),
            ],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


def _del_after_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 ثانية", callback_data="owner:ann_del:30"),
                InlineKeyboardButton(text="دقيقة", callback_data="owner:ann_del:60"),
                InlineKeyboardButton(text="5 دقائق", callback_data="owner:ann_del:300"),
            ],
            [
                InlineKeyboardButton(text="ساعة", callback_data="owner:ann_del:3600"),
                InlineKeyboardButton(text="يوم", callback_data="owner:ann_del:86400"),
            ],
            [InlineKeyboardButton(text="🔢 مخصص (ثواني)", callback_data="owner:ann_del:custom")],
            [InlineKeyboardButton(text="⏭️ بدون حذف تلقائي", callback_data="owner:ann_del:0")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


# ===== القائمة الرئيسية =====

@router.callback_query(F.data == "owner:announcements")
async def show_announcements(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()

    pool = await get_pool()
    announcements = await ann_queries.get_all_announcements(pool)

    text = f"📢 <b>الإعلانات</b> ({len(announcements)})\n━━━━━━━━━━━━━━━\nاضغط 🗑️ لحذف، أو ➕ لإضافة:"
    await callback.message.edit_text(text, reply_markup=_ann_list_kb(announcements))
    await callback.answer()


# ===== حذف =====

@router.callback_query(F.data.startswith("owner:ann_delete:"))
async def delete_announcement(callback: CallbackQuery) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    index = int(callback.data.split(":")[-1])
    pool = await get_pool()
    await ann_queries.delete_announcement(pool, index)

    announcements = await ann_queries.get_all_announcements(pool)
    await callback.message.edit_text(
        f"📢 <b>الإعلانات</b> ({len(announcements)})\n━━━━━━━━━━━━━━━",
        reply_markup=_ann_list_kb(announcements),
    )
    await callback.answer("🗑️ تم الحذف")


# ===== الخطوة 1: كلمة التشغيل =====

@router.callback_query(F.data == "owner:ann_add_trigger")
async def add_trigger_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await state.set_state(OwnerStates.waiting_announcement_trigger)
    await callback.message.edit_text("✏️ أرسل كلمة التشغيل (مثال: قوانين):", reply_markup=_cancel_kb())
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_trigger)
async def trigger_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return
    if message.chat.type != "private":
        return

    trigger = message.text.strip()

    if " " in trigger or len(trigger) > 30:
        await message.reply("❌ كلمة واحدة فقط بحد أقصى 30 حرف.", reply_markup=_cancel_kb())
        return

    pool = await get_pool()
    if await ann_queries.trigger_exists(pool, trigger):
        await message.reply("❌ هذه الكلمة مستخدمة بالفعل.", reply_markup=_cancel_kb())
        return

    # نحفظ الـ trigger فوراً في الـ state بشكل صريح
    await state.update_data(
        ann_trigger=trigger,
        ann_file_id=None,
        ann_file_type=None,
        ann_text=None,
        ann_button_text=None,
        ann_button_url=None,
        ann_pin=False,
        ann_delete_after=0,
    )
    await state.set_state(OwnerStates.waiting_announcement_media)
    await message.reply("📎 اختر نوع الوسائط:", reply_markup=_media_type_kb())


# ===== الخطوة 2: الوسائط =====

@router.callback_query(F.data.startswith("owner:ann_media:"))
async def media_type_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    media_type = callback.data.split(":")[-1]

    if media_type == "none":
        await state.update_data(ann_file_type=None, ann_file_id=None)
        await state.set_state(OwnerStates.waiting_announcement_text)
        await callback.message.edit_text("✏️ أرسل نص الإعلان:", reply_markup=_skip_kb("owner:ann_skip_text"))
    else:
        await state.update_data(ann_file_type=media_type)
        await state.set_state(OwnerStates.waiting_announcement_media)

        labels = {"photo": "🖼️ صورة", "video": "🎥 فيديو", "animation": "🎞️ GIF", "sticker": "🎭 ملصق"}
        await callback.message.edit_text(
            f"📎 أرسل {labels.get(media_type, 'الوسائط')} الآن:", reply_markup=_cancel_kb()
        )
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_media)
async def media_file_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return
    if message.chat.type != "private":
        return

    data = await state.get_data()
    file_type = data.get("ann_file_type")

    file_id = None
    if file_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif file_type == "video" and message.video:
        file_id = message.video.file_id
    elif file_type == "animation" and message.animation:
        file_id = message.animation.file_id
    elif file_type == "sticker" and message.sticker:
        file_id = message.sticker.file_id

    if file_id is None:
        await message.reply("❌ نوع الوسائط غير مطابق، أرسل النوع الصحيح:", reply_markup=_cancel_kb())
        return

    await state.update_data(ann_file_id=file_id)
    await state.set_state(OwnerStates.waiting_announcement_text)

    await message.reply("✏️ أرسل نص الإعلان (أو تخطَّ):", reply_markup=_skip_kb("owner:ann_skip_text"))


# ===== الخطوة 3: النص =====

@router.message(OwnerStates.waiting_announcement_text)
async def text_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return
    if message.chat.type != "private":
        return

    await state.update_data(ann_text=message.text)
    await state.set_state(OwnerStates.waiting_announcement_button_text)
    await message.reply("🔘 أرسل نص زر الرابط (أو تخطَّ):", reply_markup=_skip_kb("owner:ann_skip_btn"))


@router.callback_query(F.data == "owner:ann_skip_text")
async def skip_text(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_announcement_button_text)
    await callback.message.edit_text("🔘 أرسل نص زر الرابط (أو تخطَّ):", reply_markup=_skip_kb("owner:ann_skip_btn"))
    await callback.answer()


# ===== الخطوة 4: الزر =====

@router.message(OwnerStates.waiting_announcement_button_text)
async def button_text_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return
    if message.chat.type != "private":
        return

    await state.update_data(ann_button_text=message.text.strip())
    await state.set_state(OwnerStates.waiting_announcement_button_url)
    await message.reply("🔗 أرسل رابط الزر:", reply_markup=_cancel_kb())


@router.callback_query(F.data == "owner:ann_skip_btn")
async def skip_button(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_announcement_delete_after)
    await callback.message.edit_text("📌 هل تريد تثبيت الإعلان؟", reply_markup=_pin_kb())
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_button_url)
async def button_url_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return
    if message.chat.type != "private":
        return

    await state.update_data(ann_button_url=message.text.strip())
    await state.set_state(OwnerStates.waiting_announcement_delete_after)
    await message.reply("📌 هل تريد تثبيت الإعلان؟", reply_markup=_pin_kb())


# ===== الخطوة 5: التثبيت =====

@router.callback_query(F.data.startswith("owner:ann_pin:"))
async def pin_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pin = callback.data.split(":")[-1] == "yes"
    await state.update_data(ann_pin=pin)
    await state.set_state(OwnerStates.waiting_announcement_delete_after)
    await callback.message.edit_text("⏳ هل تريد حذفاً تلقائياً؟", reply_markup=_del_after_kb())
    await callback.answer()


# ===== الخطوة 6: الحذف التلقائي + حفظ =====

@router.callback_query(F.data.startswith("owner:ann_del:"))
async def delete_after_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    value = callback.data.split(":")[-1]

    if value == "custom":
        await state.set_state(OwnerStates.waiting_announcement_delete_after)
        await callback.message.edit_text("✏️ أرسل المدة بالثواني:", reply_markup=_cancel_kb())
        await callback.answer()
        return

    await _save_announcement(callback, state, int(value))


@router.message(OwnerStates.waiting_announcement_delete_after)
async def custom_del_after_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return
    if message.chat.type != "private":
        return

    if not message.text.isdigit():
        await message.reply("❌ أرسل رقماً صحيحاً.", reply_markup=_cancel_kb())
        return

    data = await state.get_data()
    pool = await get_pool()
    ann = _build_ann(data, int(message.text))
    await ann_queries.add_announcement(pool, ann)
    await state.clear()

    announcements = await ann_queries.get_all_announcements(pool)
    await message.reply(
        f"✅ تم حفظ الإعلان «{ann['trigger']}»\n\n📢 <b>الإعلانات</b> ({len(announcements)})",
        reply_markup=_ann_list_kb(announcements),
    )


async def _save_announcement(callback: CallbackQuery, state: FSMContext, delete_after: int) -> None:
    data = await state.get_data()
    pool = await get_pool()
    ann = _build_ann(data, delete_after)
    await ann_queries.add_announcement(pool, ann)
    await state.clear()

    announcements = await ann_queries.get_all_announcements(pool)
    pin_text = " (مثبّت 📌)" if ann.get("pin") else ""
    del_text = f" (يُحذف بعد {delete_after}ث)" if delete_after > 0 else ""

    await callback.message.edit_text(
        f"✅ تم حفظ الإعلان «{ann['trigger']}»{pin_text}{del_text}\n\n📢 <b>الإعلانات</b> ({len(announcements)})",
        reply_markup=_ann_list_kb(announcements),
    )
    await callback.answer()


def _build_ann(data: dict, delete_after: int) -> dict:
    """يبني قاموس الإعلان من بيانات الـ FSM state."""
    return {
        "trigger": data.get("ann_trigger", ""),
        "text": data.get("ann_text") or "",
        "file_id": data.get("ann_file_id"),
        "file_type": data.get("ann_file_type"),
        "button_text": data.get("ann_button_text"),
        "button_url": data.get("ann_button_url"),
        "pin": data.get("ann_pin", False),
        "delete_after": delete_after,
    }
