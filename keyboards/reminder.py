from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REMINDER_TIME_BTN = "🕐 Только время"
REMINDER_DATETIME_BTN = "📅 Дата и время"
REMINDER_SKIP_BTN = "⏭ Без напоминания"

REMINDER_BUTTONS = {REMINDER_TIME_BTN, REMINDER_DATETIME_BTN, REMINDER_SKIP_BTN}


def get_reminder_choice_keyboard() -> ReplyKeyboardMarkup:
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
