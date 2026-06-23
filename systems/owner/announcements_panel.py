"""
لوحة التحكم - نظام الإعلانات المتطور.

كل إعلان يمكن أن يحتوي: نص + وسائط (صورة/فيديو/GIF/ملصق) + زر رابط + تثبيت + حذف تلقائي.
تدفق إضافة إعلان جديد:
1. كلمة التشغيل
2. اختيار نوع الوسائط (أو بدون)
3. إرسال الوسائط إن وُجدت
4. النص (اختياري)
5. زر رابط (اختياري)
6. تثبيت؟ (نعم/لا)
7. حذف تلقائي؟ (مدة أو بدون)
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


def _skip_kb(next_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ تخطي", callback_data=next_cb)],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


def _ann_list_kb(announcements: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for i, ann in enumerate(announcements):
        trigger = ann.get("trigger", "؟")
        has_media = "📎" if ann.get("file_id") else ""
        has_pin = "📌" if ann.get("pin") else ""
        buttons.append([
            InlineKeyboardButton(text=f"{has_media}{has_pin} {trigger}", callback_data="owner:noop"),
            InlineKeyboardButton(text="🗑️", callback_data=f"owner:ann_delete:{i}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ إضافة إعلان", callback_data="owner:ann_add_trigger")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="owner:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _media_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🖼️ صورة", callback_data="owner:ann_media_type:photo"),
                InlineKeyboardButton(text="🎥 فيديو", callback_data="owner:ann_media_type:video"),
            ],
            [
                InlineKeyboardButton(text="🎞️ GIF", callback_data="owner:ann_media_type:animation"),
                InlineKeyboardButton(text="🎭 ملصق", callback_data="owner:ann_media_type:sticker"),
            ],
            [InlineKeyboardButton(text="⏭️ بدون وسائط", callback_data="owner:ann_media_type:none")],
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


def _delete_after_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 ثانية", callback_data="owner:ann_del_after:30"),
                InlineKeyboardButton(text="دقيقة", callback_data="owner:ann_del_after:60"),
                InlineKeyboardButton(text="5 دقائق", callback_data="owner:ann_del_after:300"),
            ],
            [
                InlineKeyboardButton(text="ساعة", callback_data="owner:ann_del_after:3600"),
                InlineKeyboardButton(text="يوم", callback_data="owner:ann_del_after:86400"),
            ],
            [InlineKeyboardButton(text="🔢 مخصص (ثواني)", callback_data="owner:ann_del_after:custom")],
            [InlineKeyboardButton(text="⏭️ بدون حذف تلقائي", callback_data="owner:ann_del_after:0")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="owner:announcements")],
        ]
    )


# ===== عرض القائمة =====

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
    text = f"📢 <b>الإعلانات</b> ({len(announcements)})\n━━━━━━━━━━━━━━━"
    await callback.message.edit_text(text, reply_markup=_ann_list_kb(announcements))
    await callback.answer("🗑️ تم الحذف")


# ===== إضافة - الخطوة 1: كلمة التشغيل =====

@router.callback_query(F.data == "owner:ann_add_trigger")
async def add_trigger_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(OwnerStates.waiting_announcement_trigger)
    await state.update_data(new_ann={})
    await callback.message.edit_text("✏️ أرسل كلمة التشغيل (مثال: قوانين):", reply_markup=_cancel_kb())
    await callback.answer()


@router.message(OwnerStates.waiting_announcement_trigger)
async def add_trigger_receive(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return

    trigger = message.text.strip()

    if " " in trigger or len(trigger) > 30:
        await message.reply("❌ كلمة التشغيل يجب أن تكون كلمة واحدة بحد أقصى 30 حرف.", reply_markup=_cancel_kb())
        return

    pool = await get_pool()
    if await ann_queries.trigger_exists(pool, trigger):
        await message.reply("❌ هذه الكلمة مستخدمة بالفعل.", reply_markup=_cancel_kb())
        return

    await state.update_data(new_ann={"trigger": trigger})
    await state.set_state(OwnerStates.waiting_announcement_media)
    await message.reply("📎 اختر نوع الوسائط:", reply_markup=_media_type_kb())


# ===== الخطوة 2: نوع الوسائط =====

@router.callback_query(F.data.startswith("owner:ann_media_type:"))
async def media_type_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    media_type = callback.data.split(":")[-1]
    data = await state.get_data()
    new_ann = data.get("new_ann", {})

    if media_type == "none":
        new_ann["file_type"] = None
        new_ann["file_id"] = None
        await state.update_data(new_ann=new_ann)
        await state.set_state(OwnerStates.waiting_announcement_text)
        await callback.message.edit_text("✏️ أرسل نص الإعلان:", reply_markup=_skip_kb("owner:ann_skip_text"))
    else:
        new_ann["file_type"] = media_type
        await state.update_data(new_ann=new_ann)
        await state.set_state(OwnerStates.waiting_announcement_media)

        type_labels = {"photo": "صورة 🖼️", "video": "فيديو 🎥", "animation": "GIF 🎞️", "sticker": "ملصق 🎭"}
        await callback.message.edit_text(
            f"📎 أرسل {type_labels.get(media_type, 'الوسائط')} الآن:",
            reply_markup=_cancel_kb(),
        )

    await callback.answer()


@router.message(OwnerStates.waiting_announcement_media)
async def media_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None):
        return

    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    file_type = new_ann.get("file_type")

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
        await message.reply("❌ نوع الوسائط غير مطابق. أرسل النوع الصحيح:", reply_markup=_cancel_kb())
        return

    new_ann["file_id"] = file_id
    await state.update_data(new_ann=new_ann)
    await state.set_state(OwnerStates.waiting_announcement_text)

    if file_type == "sticker":
        # الملصق لا يدعم نصاً، ننتقل مباشرة للزر
        await message.reply("📎 أرسل نص الزر (أو تخطَّ):", reply_markup=_skip_kb("owner:ann_skip_text"))
    else:
        await message.reply("✏️ أرسل نص الإعلان (أو تخطَّ):", reply_markup=_skip_kb("owner:ann_skip_text"))


# ===== الخطوة 3: النص =====

@router.message(OwnerStates.waiting_announcement_text)
async def text_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return

    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["text"] = message.text
    await state.update_data(new_ann=new_ann)
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

    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["button_text"] = message.text.strip()
    await state.update_data(new_ann=new_ann)
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

    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["button_url"] = message.text.strip()
    await state.update_data(new_ann=new_ann)
    await state.set_state(OwnerStates.waiting_announcement_delete_after)
    await message.reply("📌 هل تريد تثبيت الإعلان؟", reply_markup=_pin_kb())


# ===== الخطوة 5: التثبيت =====

@router.callback_query(F.data.startswith("owner:ann_pin:"))
async def pin_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pin = callback.data.split(":")[-1] == "yes"
    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["pin"] = pin
    await state.update_data(new_ann=new_ann)
    await state.set_state(OwnerStates.waiting_announcement_delete_after)
    await callback.message.edit_text("⏳ هل تريد حذفاً تلقائياً؟", reply_markup=_delete_after_kb())
    await callback.answer()


# ===== الخطوة 6: الحذف التلقائي =====

@router.callback_query(F.data.startswith("owner:ann_del_after:"))
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

    await _finalize_announcement(callback, state, int(value))


@router.message(OwnerStates.waiting_announcement_delete_after)
async def custom_delete_after_received(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id if message.from_user else None) or not message.text:
        return

    if not message.text.isdigit():
        await message.reply("❌ أرسل رقماً صحيحاً بالثواني.", reply_markup=_cancel_kb())
        return

    await _finalize_announcement_from_message(message, state, int(message.text))


async def _finalize_announcement(callback: CallbackQuery, state: FSMContext, delete_after: int) -> None:
    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["delete_after"] = delete_after

    pool = await get_pool()
    await ann_queries.add_announcement(pool, new_ann)
    await state.clear()

    announcements = await ann_queries.get_all_announcements(pool)
    trigger = new_ann.get("trigger", "")
    pin_text = " (مثبّت 📌)" if new_ann.get("pin") else ""
    del_text = f" (يُحذف بعد {delete_after} ثانية)" if delete_after > 0 else ""

    await callback.message.edit_text(
        f"✅ تم حفظ الإعلان «{trigger}»{pin_text}{del_text}\n\n📢 <b>الإعلانات</b> ({len(announcements)})\n━━━━━━━━━━━━━━━",
        reply_markup=_ann_list_kb(announcements),
    )
    await callback.answer()


async def _finalize_announcement_from_message(message: Message, state: FSMContext, delete_after: int) -> None:
    data = await state.get_data()
    new_ann = data.get("new_ann", {})
    new_ann["delete_after"] = delete_after

    pool = await get_pool()
    await ann_queries.add_announcement(pool, new_ann)
    await state.clear()

    announcements = await ann_queries.get_all_announcements(pool)
    trigger = new_ann.get("trigger", "")

    await message.reply(
        f"✅ تم حفظ الإعلان «{trigger}»\n\n📢 <b>الإعلانات</b> ({len(announcements)})\n━━━━━━━━━━━━━━━",
        reply_markup=_ann_list_kb(announcements),
    )
