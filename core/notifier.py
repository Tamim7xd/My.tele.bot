"""
المرسل المركزي لجميع الإشعارات.
كل نظام يستورد دالة send_notification من هنا لإرسال إشعاراته للمجموعة
أو رسالة خاصة للعضو، دون الحاجة لتكرار كود الإرسال في كل نظام.

مستقبلاً: لتغيير شكل/تصميم جميع الإشعارات دفعة واحدة، يكفي تعديل
هذا الملف فقط دون لمس أي نظام آخر.
"""

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup


async def send_group_notification(
    bot: Bot,
    group_id: int,
    text: str,
    pin: bool = False,
    gif_url: str | None = None,
) -> None:
    """
    يرسل إشعاراً لمجموعة معينة.

    المعاملات:
        bot: نسخة البوت
        group_id: آيدي المجموعة
        text: نص الإشعار (جاهز ومنسق من النظام المستدعي)
        pin: تثبيت الرسالة أم لا
        gif_url: رابط GIF اختياري لإرساله مع الرسالة
    """
    if gif_url:
        message = await bot.send_animation(
            chat_id=group_id,
            animation=gif_url,
            caption=text,
        )
    else:
        message = await bot.send_message(
            chat_id=group_id,
            text=text,
        )

    if pin:
        await bot.pin_chat_message(chat_id=group_id, message_id=message.message_id)


async def send_private_notification(
    bot: Bot,
    user_id: int,
    text: str,
) -> bool:
    """
    يرسل رسالة خاصة لعضو معين (مثل إشعار انتهاء كتم أو حظر).

    يرجع True لو نجح الإرسال، و False لو فشل
    (مثلاً العضو لم يبدأ محادثة مع البوت).
    """
    try:
        await bot.send_message(chat_id=user_id, text=text)
        return True
    except Exception:
        return False


async def send_with_buttons(
    bot: Bot,
    chat_id: int,
    text: str,
    keyboard: InlineKeyboardMarkup,
):
    """
    يرسل رسالة مع أزرار Inline.
    تستخدمه جميع الأنظمة لإرسال القوائم والأزرار التفاعلية.
    """
    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
    )
