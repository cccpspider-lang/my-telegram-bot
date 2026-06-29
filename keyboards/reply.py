from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MY_TASKS_BTN = "📋 Мои задачи"
ADD_TASK_BTN = "➕ Добавить задачу"
DELETE_TASK_BTN = "🗑 Удалить задачу"
HELP_BTN = "ℹ️ Помощь"
SUPPORT_BTN = "❤️ Поддержка"
BACK_BTN = "⬅️ Назад"

MENU_BUTTONS = {
    MY_TASKS_BTN,
    ADD_TASK_BTN,
    DELETE_TASK_BTN,
    HELP_BTN,
    SUPPORT_BTN,
}


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MY_TASKS_BTN)],
            [KeyboardButton(text=ADD_TASK_BTN)],
            [KeyboardButton(text=DELETE_TASK_BTN)],
            [KeyboardButton(text=HELP_BTN)],
            [KeyboardButton(text=SUPPORT_BTN)],
        ],
        resize_keyboard=True,
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BTN)]],
        resize_keyboard=True,
    )
