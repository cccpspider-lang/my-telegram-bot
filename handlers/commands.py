from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from datetime import datetime

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
from keyboards.task import REPEAT_BUTTONS, get_repeat_keyboard
from reminders.constants import REPEAT_BUTTON_TO_TYPE
from utils.datetime_parser import parse_strict_date_time
from utils.formatters import (
    format_back_to_menu,
    format_empty_tasks,
    format_help,
    format_invalid_datetime,
    format_no_tasks_to_delete,
    format_prompt_add_task,
    format_prompt_datetime,
    format_prompt_repeat,
    format_support,
    format_task_saved,
    format_tasks_list,
    format_welcome,
    get_user_name,
)

router = Router()
HTML = {"parse_mode": "HTML"}


def get_user_id(message: Message) -> int:
    return message.from_user.id


async def go_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(format_back_to_menu(), reply_markup=get_main_menu())


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
    await state.set_state(TaskStates.waiting_for_datetime)
    await message.answer(
        format_prompt_datetime(),
        reply_markup=get_back_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_datetime, F.text)
async def process_datetime(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await go_main_menu(message, state)
        return
    if message.text in MENU_BUTTONS | REPEAT_BUTTONS:
        await message.answer(
            "📅 Введите дату и время.",
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

    await state.update_data(remind_at=remind_at.isoformat())
    await state.set_state(TaskStates.waiting_for_repeat_type)
    await message.answer(
        format_prompt_repeat(),
        reply_markup=get_repeat_keyboard(),
        **HTML,
    )


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
