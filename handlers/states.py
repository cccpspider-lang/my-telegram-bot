from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_reminder_choice = State()
    waiting_for_time = State()
    waiting_for_datetime = State()
    waiting_for_task_id = State()
    waiting_for_clear_confirm = State()

