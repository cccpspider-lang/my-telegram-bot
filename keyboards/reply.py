from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ADD_TASK_BTN = "📝 Добавить задачу"
MY_TASKS_BTN = "📋 Мои задачи"
DELETE_TASK_BTN = "❌ Удалить задачу"
HELP_BTN = "ℹ️ Помощь"

MENU_BUTTONS = {ADD_TASK_BTN, MY_TASKS_BTN, DELETE_TASK_BTN, HELP_BTN}


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADD_TASK_BTN),
                KeyboardButton(text=MY_TASKS_BTN),
            ],
            [
                KeyboardButton(text=DELETE_TASK_BTN),
                KeyboardButton(text=HELP_BTN),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или введите команду…",
    )
