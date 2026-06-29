from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ADD_TASK_BTN = "📝 Добавить задачу"
MY_TASKS_BTN = "📋 Мои задачи"
ADD_REMINDER_BTN = "🔔 Напоминания"
MY_REMINDERS_BTN = "📋 Мои напоминания"
DELETE_TASK_BTN = "❌ Удалить задачу"
DELETE_REMINDER_BTN = "🗑 Удалить напоминание"
HELP_BTN = "ℹ️ Помощь"

MENU_BUTTONS = {
    ADD_TASK_BTN,
    MY_TASKS_BTN,
    ADD_REMINDER_BTN,
    MY_REMINDERS_BTN,
    DELETE_TASK_BTN,
    DELETE_REMINDER_BTN,
    HELP_BTN,
}


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADD_TASK_BTN),
                KeyboardButton(text=MY_TASKS_BTN),
            ],
            [
                KeyboardButton(text=ADD_REMINDER_BTN),
                KeyboardButton(text=MY_REMINDERS_BTN),
            ],
            [
                KeyboardButton(text=DELETE_TASK_BTN),
                KeyboardButton(text=DELETE_REMINDER_BTN),
            ],
            [KeyboardButton(text=HELP_BTN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или введите команду…",
    )
