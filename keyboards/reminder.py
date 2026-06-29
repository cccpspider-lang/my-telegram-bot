from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from keyboards.reply import BACK_BTN

ADD_REMINDER_BTN = "🔔 Добавить напоминание"
SKIP_REMINDER_BTN = "⏩ Без напоминания"

TASK_REMINDER_BUTTONS = {
    ADD_REMINDER_BTN,
    SKIP_REMINDER_BTN,
    BACK_BTN,
}


def get_task_reminder_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_REMINDER_BTN)],
            [
                KeyboardButton(text=SKIP_REMINDER_BTN),
                KeyboardButton(text=BACK_BTN),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )
