"""
حالات المحادثة (FSM States) لنظام الحظر/الكتم/التحذير.

كل التفاعل يتم بالأزرار (Inline)، نُبقي حالة واحدة فقط
لتخزين سياق العملية الجارية في FSM context.
"""

from aiogram.fsm.state import State, StatesGroup


class ModerationStates(StatesGroup):
    in_progress = State()
