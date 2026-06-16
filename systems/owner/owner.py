"""
لوحة تحكم المالك الرئيسية
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from systems.owner.utils import owner_only

router = Router()


@router.callback_query(F.data == "owner_panel")
@owner_only
async def owner_panel(callback: CallbackQuery):
    """لوحة التحكم الرئيسية"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👥 إدارة الأعضاء", callback_data="members_panel")
    builder.button(text="📋 الأرشيف", callback_data="archive_panel")
    builder.button(text="👮‍♂️ المشرفين", callback_data="moderators_panel")
    builder.button(text="📊 المستويات", callback_data="levels_panel")
    builder.button(text="⚖️ الإشراف", callback_data="moderation_panel")
    builder.button(text="📢 الإعلانات", callback_data="announcements_panel")
    builder.button(text="🛡️ الحماية", callback_data="protection_panel")
    
    # ⭐ زر نظام العضويات الإدارية الجديد
    builder.button(text="👑 إدارة العضويات", callback_data="ranks_panel")
    
    builder.button(text="🔙 رجوع", callback_data="back_to_main")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🔐 <b>لوحة تحكم المالك</b>\n\n"
        "اختر النظام الذي تريد إدارته:",
        reply_markup=builder.as_markup()
    )
