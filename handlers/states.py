from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_datetime = State()
    waiting_for_repeat_type = State()
