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

__all__ = ["REPEAT_BUTTONS", "get_delete_tasks_keyboard", "get_repeat_keyboard"]


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
