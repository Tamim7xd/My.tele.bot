"""
أدوات مساعدة للوحة التحكم - التحقق من الصلاحيات
"""

from functools import wraps
from aiogram.types import CallbackQuery, Message

from core.config import OWNER_ID
from core.database import has_permission, get_pool


def owner_only(handler):
    """مُزيّن: فقط المالك يمكنه الوصول"""
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        
        if user_id != OWNER_ID:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ فقط المالك!", show_alert=True)
            else:
                await event.answer("⛔ ليس لديك صلاحية!")
            return
        
        return await handler(event, *args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """مُزيّن: يتطلب صلاحية معينة"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(event, *args, **kwargs):
            user_id = event.from_user.id
            
            # المالك يملك كل شيء
            if user_id == OWNER_ID:
                return await handler(event, *args, **kwargs)
            
            pool = await get_pool()
            has = await has_permission(pool, user_id, permission)
            
            if not has:
                if isinstance(event, CallbackQuery):
                    await event.answer(f"⛔ تحتاج صلاحية: {permission}", show_alert=True)
                else:
                    await event.answer(f"⛔ ليس لديك صلاحية: {permission}")
                return
            
            return await handler(event, *args, **kwargs)
        return wrapper
    return decorator


def admin_only(handler):
    """مُزيّن: الأدمن فأعلى (manage_staff)"""
    return require_permission("manage_staff")(handler)
