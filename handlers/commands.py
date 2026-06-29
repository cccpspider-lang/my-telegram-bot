from datetime import date, datetime
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from config import SUPPORT_USERNAME
from handlers.states import TaskStates
from keyboards import (
    ADD_TASK_BTN,
    BACK_BTN,
    DELETE_TASK_BTN,
    HELP_BTN,
    MENU_BUTTONS,
    MY_TASKS_BTN,
    SUPPORT_BTN,
    get_back_keyboard,
    get_main_menu,
)
from keyboards.task import (
    DATE_BUTTONS,
    DATE_MANUAL_BTN,
    DATE_TODAY_BTN,
    DATE_TOMORROW_BTN,
    REPEAT_BUTTONS,
    get_date_choice_keyboard,
    get_repeat_keyboard,
)
from reminders.constants import REPEAT_BUTTON_TO_TYPE
from utils.datetime_parser import is_valid_time_format, parse_moscow_time, parse_strict_date_time
from utils.formatters import (
    format_back_to_menu,
    format_empty_tasks,
    format_help,
    format_invalid_datetime,
    format_invalid_time,
    format_no_tasks_to_delete,
    format_prompt_add_task,
    format_prompt_date_choice,
    format_prompt_manual_datetime,
    format_prompt_repeat,
    format_prompt_time_msk,
    format_support,
    format_task_saved,
    format_tasks_list,
    format_time_in_past,
    format_welcome,
    get_user_name,
)
from utils.timezone import today_moscow, tomorrow_moscow

router = Router()
HTML = {"parse_mode": "HTML"}
logger = logging.getLogger(__name__)


async def log_fsm(message: Message, state: FSMContext, step: str) -> None:
    current_state = await state.get_state()
    logger.info(
        "[%s] FSM state: %s | user_id: %s | message: %r",
        step,
        current_state,
        message.from_user.id if message.from_user else None,
        message.text,
    )


def get_user_id(message: Message) -> int:
    return message.from_user.id


async def go_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(format_back_to_menu(), reply_markup=get_main_menu())


async def proceed_to_repeat_step(message: Message, state: FSMContext, remind_at: datetime) -> None:
    await state.update_data(remind_at=remind_at.isoformat())
    await state.set_state(TaskStates.waiting_for_repeat_type)
    await message.answer(
        format_prompt_repeat(),
        reply_markup=get_repeat_keyboard(),
        **HTML,
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        format_welcome(get_user_name(message)),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(F.text == HELP_BTN)
async def btn_help(message: Message) -> None:
    await message.answer(format_help(), reply_markup=get_main_menu(), **HTML)


@router.message(F.text == SUPPORT_BTN)
async def btn_support(message: Message) -> None:
    await message.answer(
        format_support(SUPPORT_USERNAME),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(F.text == MY_TASKS_BTN)
async def btn_my_tasks(message: Message) -> None:
    tasks = db.get_tasks(get_user_id(message))
    if not tasks:
        await message.answer(format_empty_tasks(), reply_markup=get_main_menu(), **HTML)
        return
    await message.answer(
        format_tasks_list(tasks),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(F.text == ADD_TASK_BTN)
async def btn_add_task(message: Message, state: FSMContext) -> None:
    await state.set_state(TaskStates.waiting_for_task_text)
    await message.answer(
        format_prompt_add_task(),
        reply_markup=get_back_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_task_text, F.text)
async def process_task_text(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return
    if message.text in MENU_BUTTONS:
        await message.answer(
            "✏️ Введите текст задачи.",
            reply_markup=get_back_keyboard(),
        )
        return

    text = message.text.strip()
    if not text:
        await message.answer(
            "⚠️ Текст не может быть пустым.",
            reply_markup=get_back_keyboard(),
        )
        return

    await state.update_data(task_text=text)
    await state.set_state(TaskStates.waiting_for_date_choice)
    await message.answer(
        format_prompt_date_choice(),
        reply_markup=get_date_choice_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_date_choice, F.text)
async def process_date_choice(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return

    if message.text == DATE_TODAY_BTN:
        await state.update_data(target_date=today_moscow().isoformat())
        await state.set_state(TaskStates.waiting_for_time)
        logger.info(
            "Set FSM state to waiting_for_time for user %s, target_date=%s",
            message.from_user.id,
            today_moscow().isoformat(),
        )
        await message.answer(format_prompt_time_msk(), reply_markup=get_back_keyboard(), **HTML)
        return

    if message.text == DATE_TOMORROW_BTN:
        await state.update_data(target_date=tomorrow_moscow().isoformat())
        await state.set_state(TaskStates.waiting_for_time)
        logger.info(
            "Set FSM state to waiting_for_time for user %s, target_date=%s",
            message.from_user.id,
            tomorrow_moscow().isoformat(),
        )
        await message.answer(format_prompt_time_msk(), reply_markup=get_back_keyboard(), **HTML)
        return

    if message.text == DATE_MANUAL_BTN:
        await state.set_state(TaskStates.waiting_for_manual_datetime)
        await message.answer(
            format_prompt_manual_datetime(),
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    await message.answer(
        "Выберите дату из меню.",
        reply_markup=get_date_choice_keyboard(),
    )


@router.message(TaskStates.waiting_for_time, F.text)
async def process_time(message: Message, state: FSMContext) -> None:
    await log_fsm(message, state, "process_time")

    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return
    if message.text in MENU_BUTTONS | DATE_BUTTONS | REPEAT_BUTTONS:
        await message.answer(
            "🕐 Введите время по Москве (МСК).",
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    if not is_valid_time_format(message.text):
        logger.warning("Invalid time format from user %s: %r", message.from_user.id, message.text)
        await message.answer(
            format_invalid_time(),
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    data = await state.get_data()
    target_date = date.fromisoformat(data["target_date"])
    remind_at = parse_moscow_time(message.text, target_date)
    if remind_at is None:
        logger.warning("Time in past from user %s: %r", message.from_user.id, message.text)
        await message.answer(
            format_time_in_past(),
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    logger.info("Time accepted for user %s: %s", message.from_user.id, remind_at)
    await proceed_to_repeat_step(message, state, remind_at)


@router.message(TaskStates.waiting_for_manual_datetime, F.text)
async def process_manual_datetime(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return
    if message.text in MENU_BUTTONS | DATE_BUTTONS | REPEAT_BUTTONS:
        await message.answer(
            "✍️ Введите дату и время по Москве (МСК).",
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    remind_at = parse_strict_date_time(message.text)
    if remind_at is None:
        await message.answer(
            format_invalid_datetime(),
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    await proceed_to_repeat_step(message, state, remind_at)


@router.message(TaskStates.waiting_for_repeat_type, F.text)
async def process_repeat_type(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return

    repeat_type = REPEAT_BUTTON_TO_TYPE.get(message.text)
    if repeat_type is None:
        await message.answer(
            "Выберите периодичность из меню.",
            reply_markup=get_repeat_keyboard(),
        )
        return

    data = await state.get_data()
    remind_at = datetime.fromisoformat(data["remind_at"])
    task_text = data["task_text"]
    task_number = db.add_task(
        get_user_id(message),
        task_text,
        remind_at,
        repeat_type,
    )
    await state.clear()
    await message.answer(
        format_task_saved(task_number, task_text, remind_at, repeat_type),
        reply_markup=get_main_menu(),
        **HTML,
    )
