from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from keyboards.reply import BACK_BTN
from reminders.constants import (
    REPEAT_BTN_DAILY,
    REPEAT_BTN_MONTHLY,
    REPEAT_BTN_NONE,
    REPEAT_BTN_ONCE,
    REPEAT_BTN_WEEKLY,
    REPEAT_BUTTONS,
)

DATE_TODAY_BTN = "📅 Сегодня"
DATE_TOMORROW_BTN = "🌅 Завтра"
DATE_MANUAL_BTN = "✍️ Ввести вручную"
DATE_PERMANENT_BTN = "♾️ Постоянная"

DATE_BUTTONS = {
    DATE_TODAY_BTN,
    DATE_TOMORROW_BTN,
    DATE_MANUAL_BTN,
    DATE_PERMANENT_BTN,
    BACK_BTN,
}

__all__ = [
    "DATE_BUTTONS",
    "DATE_MANUAL_BTN",
    "DATE_PERMANENT_BTN",
    "DATE_TODAY_BTN",
    "DATE_TOMORROW_BTN",
    "REPEAT_BUTTONS",
    "get_complete_tasks_keyboard",
    "get_date_choice_keyboard",
    "get_delete_tasks_keyboard",
    "get_repeat_keyboard",
]


def get_date_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DATE_TODAY_BTN), KeyboardButton(text=DATE_TOMORROW_BTN)],
            [KeyboardButton(text=DATE_MANUAL_BTN), KeyboardButton(text=DATE_PERMANENT_BTN)],
            [KeyboardButton(text=BACK_BTN)],
        ],
        resize_keyboard=True,
    )


def get_repeat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REPEAT_BTN_ONCE)],
            [KeyboardButton(text=REPEAT_BTN_DAILY)],
            [KeyboardButton(text=REPEAT_BTN_WEEKLY)],
            [KeyboardButton(text=REPEAT_BTN_MONTHLY)],
            [KeyboardButton(text=REPEAT_BTN_NONE)],
            [KeyboardButton(text=BACK_BTN)],
        ],
        resize_keyboard=True,
    )


def get_delete_tasks_keyboard(tasks: list) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for task in tasks:
        row.append(
            InlineKeyboardButton(
                text=str(task["task_number"]),
                callback_data=f"delete_task:{task['task_number']}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text="Назад", callback_data="delete_task:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_complete_tasks_keyboard(tasks: list) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for task in tasks:
        row.append(
            InlineKeyboardButton(
                text=str(task["task_number"]),
                callback_data=f"complete_task:{task['task_number']}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text="Назад", callback_data="complete_task:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
