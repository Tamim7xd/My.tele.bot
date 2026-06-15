"""
نظام الإعلانات (announcements) - استعلامات/تخزين.

كل الإعلانات تُخزَّن في جدول settings تحت مفتاح واحد "announcements"
كقائمة JSON من القواميس، كل قاموس بهذا الشكل:

{
    "trigger": "قوانين",          # الكلمة التي يكتبها العضو لتشغيل الإعلان
    "text": "...",                 # النص (قد يكون فارغاً)
    "file_id": null,               # file_id لصورة/GIF/ملصق (مرحلة لاحقة)
    "file_type": null,             # "photo" / "animation" / "sticker" (مرحلة لاحقة)
    "delete_after": 0,             # ثواني، 0 = بلا حذف
    "button_text": null,           # نص الزر (مرحلة لاحقة)
    "button_url": null,            # رابط الزر (مرحلة لاحقة)
}

استخدام إعدادات key-value المشتركة (core/database.py get_setting/set_setting)
يجنبنا الحاجة لجدول جديد.
"""

import asyncpg

from core.database import get_setting, set_setting


ANNOUNCEMENTS_KEY = "announcements"


async def get_all_announcements(pool: asyncpg.Pool) -> list[dict]:
    """يرجع كل الإعلانات المحفوظة."""
    return await get_setting(pool, ANNOUNCEMENTS_KEY, [])


async def get_announcement_by_trigger(pool: asyncpg.Pool, trigger: str) -> dict | None:
    """يبحث عن إعلان بأمر تشغيل معين."""
    announcements = await get_all_announcements(pool)

    for ann in announcements:
        if ann.get("trigger") == trigger:
            return ann

    return None


async def trigger_exists(pool: asyncpg.Pool, trigger: str, exclude_index: int | None = None) -> bool:
    """يتحقق إن كان أمر التشغيل مستخدماً بالفعل (لمنع التكرار)."""
    announcements = await get_all_announcements(pool)

    for i, ann in enumerate(announcements):
        if exclude_index is not None and i == exclude_index:
            continue
        if ann.get("trigger") == trigger:
            return True

    return False


async def add_announcement(pool: asyncpg.Pool, announcement: dict) -> None:
    """يضيف إعلاناً جديداً."""
    announcements = await get_all_announcements(pool)
    announcements.append(announcement)
    await set_setting(pool, ANNOUNCEMENTS_KEY, announcements)


async def update_announcement(pool: asyncpg.Pool, index: int, announcement: dict) -> None:
    """يحدّث إعلاناً موجوداً عبر فهرسه في القائمة."""
    announcements = await get_all_announcements(pool)

    if 0 <= index < len(announcements):
        announcements[index] = announcement
        await set_setting(pool, ANNOUNCEMENTS_KEY, announcements)


async def delete_announcement(pool: asyncpg.Pool, index: int) -> None:
    """يحذف إعلاناً عبر فهرسه في القائمة."""
    announcements = await get_all_announcements(pool)

    if 0 <= index < len(announcements):
        announcements.pop(index)
        await set_setting(pool, ANNOUNCEMENTS_KEY, announcements)
