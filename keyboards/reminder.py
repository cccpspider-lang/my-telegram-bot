from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from reminders.constants import REPEAT_LABELS

REMINDER_TIME_BTN = "🕐 Только время"
REMINDER_DATETIME_BTN = "📅 Дата и время"
REMINDER_SKIP_BTN = "⏭ Без напоминания"

TASK_REMINDER_BUTTONS = {
    REMINDER_TIME_BTN,
    REMINDER_DATETIME_BTN,
    REMINDER_SKIP_BTN,
}

REPEAT_BUTTONS = set(REPEAT_LABELS.values())
REPEAT_BUTTON_TO_TYPE = {label: key for key, label in REPEAT_LABELS.items()}


def get_task_reminder_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=REMINDER_TIME_BTN),
                KeyboardButton(text=REMINDER_DATETIME_BTN),
            ],
            [KeyboardButton(text=REMINDER_SKIP_BTN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите тип напоминания…",
    )


def get_repeat_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REPEAT_LABELS["once"])],
            [
                KeyboardButton(text=REPEAT_LABELS["daily"]),
                KeyboardButton(text=REPEAT_LABELS["weekly"]),
            ],
            [KeyboardButton(text=REPEAT_LABELS["monthly"])],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите периодичность…",
    )
