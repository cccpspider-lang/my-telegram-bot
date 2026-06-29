from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from datetime import datetime

from handlers.states import ReminderStates
from keyboards import (
    ADD_REMINDER_BTN,
    DELETE_REMINDER_BTN,
    MENU_BUTTONS,
    MY_REMINDERS_BTN,
    get_main_menu,
)
from keyboards.reminder import (
    REPEAT_BUTTONS,
    REPEAT_BUTTON_TO_TYPE,
    get_repeat_type_keyboard,
)
from reminders import repository as reminder_repo
from services.context import get_reminder_service
from utils.datetime_parser import parse_strict_date_time
from utils.formatters import (
    format_empty_reminders,
    format_invalid_strict_datetime,
    format_no_reminders_to_delete,
    format_prompt_add_reminder,
    format_prompt_delete_reminder,
    format_prompt_reminder_datetime,
    format_prompt_reminder_repeat,
    format_reminder_created,
    format_reminder_deleted,
    format_reminder_not_found,
    format_reminders_list,
)

router = Router()
HTML = {"parse_mode": "HTML"}


def get_telegram_user_id(message: Message) -> int:
    return message.from_user.id


async def show_reminders(message: Message) -> None:
    user_id = get_telegram_user_id(message)
    reminders = reminder_repo.get_user_reminders(user_id)

    if not reminders:
        await message.answer(
            format_empty_reminders(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await message.answer(
        format_reminders_list(reminders),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(Command("reminders"))
@router.message(F.text == MY_REMINDERS_BTN)
async def cmd_my_reminders(message: Message) -> None:
    await show_reminders(message)


@router.message(F.text == ADD_REMINDER_BTN)
async def btn_add_reminder(message: Message, state: FSMContext) -> None:
    await state.set_state(ReminderStates.waiting_for_text)
    await message.answer(
        format_prompt_add_reminder(),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(ReminderStates.waiting_for_text, F.text)
async def process_reminder_text(message: Message, state: FSMContext) -> None:
    if message.text in MENU_BUTTONS:
        await message.answer(
            "✏️ Сначала введите текст напоминания или отправьте /start.",
            reply_markup=get_main_menu(),
        )
        return

    text = message.text.strip()
    if not text:
        await message.answer(
            "⚠️ Текст не может быть пустым. Попробуйте ещё раз:",
            reply_markup=get_main_menu(),
        )
        return

    await state.update_data(reminder_text=text)
    await state.set_state(ReminderStates.waiting_for_datetime)
    await message.answer(format_prompt_reminder_datetime(), **HTML)


@router.message(ReminderStates.waiting_for_datetime, F.text)
async def process_reminder_datetime(message: Message, state: FSMContext) -> None:
    if message.text in MENU_BUTTONS | REPEAT_BUTTONS:
        await message.answer(
            "📅 Введите дату и время или /start для отмены.",
            **HTML,
        )
        return

    remind_at = parse_strict_date_time(message.text)
    if remind_at is None:
        await message.answer(format_invalid_strict_datetime(), **HTML)
        return

    await state.update_data(remind_at=remind_at.isoformat())
    await state.set_state(ReminderStates.waiting_for_repeat_type)
    await message.answer(
        format_prompt_reminder_repeat(),
        reply_markup=get_repeat_type_keyboard(),
        **HTML,
    )


@router.message(ReminderStates.waiting_for_repeat_type, F.text)
async def process_reminder_repeat(message: Message, state: FSMContext) -> None:
    repeat_type = REPEAT_BUTTON_TO_TYPE.get(message.text)
    if repeat_type is None:
        await message.answer(
            "Выберите периодичность из меню или /start для отмены.",
            reply_markup=get_repeat_type_keyboard(),
        )
        return

    data = await state.get_data()
    user_id = get_telegram_user_id(message)
    text = data["reminder_text"]
    remind_at = data["remind_at"]

    remind_dt = datetime.fromisoformat(remind_at)
    _, reminder_number = await get_reminder_service().schedule(
        user_id=user_id,
        message=text,
        remind_at=remind_dt,
        repeat_type=repeat_type,
    )

    await state.clear()
    await message.answer(
        format_reminder_created(reminder_number, text, remind_dt, repeat_type),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(F.text == DELETE_REMINDER_BTN)
async def btn_delete_reminder(message: Message, state: FSMContext) -> None:
    user_id = get_telegram_user_id(message)
    reminders = reminder_repo.get_user_reminders(user_id)

    if not reminders:
        await message.answer(
            format_no_reminders_to_delete(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await state.set_state(ReminderStates.waiting_for_delete_id)
    await message.answer(
        format_prompt_delete_reminder(reminders),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(ReminderStates.waiting_for_delete_id, F.text)
async def process_reminder_delete(message: Message, state: FSMContext) -> None:
    if message.text in MENU_BUTTONS:
        await message.answer(
            "🔢 Введите номер напоминания или /start для отмены.",
            reply_markup=get_main_menu(),
        )
        return

    if not message.text.isdigit():
        await message.answer(
            "⚠️ Введите число — номер напоминания из списка.",
            reply_markup=get_main_menu(),
        )
        return

    reminder_number = int(message.text)
    deleted = reminder_repo.delete_user_reminder(
        get_telegram_user_id(message),
        reminder_number,
    )
    await state.clear()

    if deleted:
        await message.answer(
            format_reminder_deleted(reminder_number),
            reply_markup=get_main_menu(),
            **HTML,
        )
    else:
        await message.answer(
            format_reminder_not_found(reminder_number),
            reply_markup=get_main_menu(),
            **HTML,
        )
