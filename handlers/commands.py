from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from handlers.states import TaskStates
from keyboards import (
    ADD_TASK_BTN,
    DELETE_TASK_BTN,
    HELP_BTN,
    MENU_BUTTONS,
    MY_TASKS_BTN,
    get_main_menu,
)
from keyboards.reminder import (
    REMINDER_BUTTONS,
    REMINDER_DATETIME_BTN,
    REMINDER_SKIP_BTN,
    REMINDER_TIME_BTN,
    get_reminder_choice_keyboard,
)
from services.context import get_reminder_service
from utils.datetime_parser import parse_date_time, parse_time_only
from utils.formatters import (
    format_clear_cancelled,
    format_clear_confirm,
    format_clear_done,
    format_clear_empty,
    format_empty_tasks,
    format_help,
    format_invalid_datetime,
    format_invalid_time,
    format_no_tasks_to_delete,
    format_prompt_add_task,
    format_prompt_datetime,
    format_prompt_delete_task,
    format_prompt_time,
    format_reminder_choice,
    format_task_added,
    format_task_deleted,
    format_task_not_found,
    format_tasks_list,
    format_welcome,
    get_user_name,
)

router = Router()
HTML = {"parse_mode": "HTML"}


def get_telegram_user_id(message: Message) -> int:
    return message.from_user.id


async def show_tasks(message: Message) -> None:
    user_id = get_telegram_user_id(message)
    tasks = db.get_tasks(user_id)

    if not tasks:
        await message.answer(
            format_empty_tasks(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await message.answer(
        format_tasks_list(tasks),
        reply_markup=get_main_menu(),
        **HTML,
    )


async def show_help(message: Message) -> None:
    await message.answer(
        format_help(),
        reply_markup=get_main_menu(),
        **HTML,
    )


async def start_reminder_setup(
    message: Message,
    state: FSMContext,
    task_number: int,
    task_id: int,
    task_text: str,
) -> None:
    await state.set_state(TaskStates.waiting_for_reminder_choice)
    await state.update_data(
        task_number=task_number,
        task_id=task_id,
        task_text=task_text,
    )
    await message.answer(
        format_reminder_choice(task_number, task_text),
        reply_markup=get_reminder_choice_keyboard(),
        **HTML,
    )


async def finish_task_creation(
    message: Message,
    state: FSMContext,
    remind_at=None,
) -> None:
    data = await state.get_data()
    task_number = data["task_number"]
    task_text = data["task_text"]
    task_id = data["task_id"]
    user_id = get_telegram_user_id(message)

    if remind_at is not None:
        await get_reminder_service().schedule(
            user_id=user_id,
            message=task_text,
            remind_at=remind_at,
            task_id=task_id,
        )

    await state.clear()
    await message.answer(
        format_task_added(task_number, task_text, remind_at),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = get_user_name(message)
    await message.answer(
        format_welcome(name),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(Command("help"))
@router.message(F.text == HELP_BTN)
async def cmd_help(message: Message) -> None:
    await show_help(message)


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    await show_tasks(message)


@router.message(F.text == MY_TASKS_BTN)
async def btn_my_tasks(message: Message) -> None:
    await show_tasks(message)


@router.message(F.text == ADD_TASK_BTN)
async def btn_add_task(message: Message, state: FSMContext) -> None:
    await state.set_state(TaskStates.waiting_for_task_text)
    await message.answer(
        format_prompt_add_task(),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_task_text, F.text)
async def process_task_text(message: Message, state: FSMContext) -> None:
    if message.text in MENU_BUTTONS:
        await message.answer(
            "✏️ Сначала введите текст задачи или отправьте /start для отмены.",
            reply_markup=get_main_menu(),
        )
        return

    task_text = message.text.strip()
    if not task_text:
        await message.answer(
            "⚠️ Текст не может быть пустым. Попробуйте ещё раз:",
            reply_markup=get_main_menu(),
        )
        return

    user_id = get_telegram_user_id(message)
    task_number, task_id = db.add_task(user_id, task_text)
    await start_reminder_setup(message, state, task_number, task_id, task_text)


@router.message(TaskStates.waiting_for_reminder_choice, F.text)
async def process_reminder_choice(message: Message, state: FSMContext) -> None:
    choice = message.text

    if choice == REMINDER_TIME_BTN:
        await state.set_state(TaskStates.waiting_for_time)
        await message.answer(format_prompt_time(), **HTML)
        return

    if choice == REMINDER_DATETIME_BTN:
        await state.set_state(TaskStates.waiting_for_datetime)
        await message.answer(format_prompt_datetime(), **HTML)
        return

    if choice == REMINDER_SKIP_BTN:
        await finish_task_creation(message, state)
        return

    await message.answer(
        "Выберите вариант из меню или отправьте /start для отмены.",
        reply_markup=get_reminder_choice_keyboard(),
    )


@router.message(TaskStates.waiting_for_time, F.text)
async def process_reminder_time(message: Message, state: FSMContext) -> None:
    if message.text in REMINDER_BUTTONS | MENU_BUTTONS:
        await message.answer(
            "🕐 Введите время в формате <code>14:30</code> или /start для отмены.",
            **HTML,
        )
        return

    remind_at = parse_time_only(message.text)
    if remind_at is None:
        await message.answer(format_invalid_time(), **HTML)
        return

    await finish_task_creation(message, state, remind_at)


@router.message(TaskStates.waiting_for_datetime, F.text)
async def process_reminder_datetime(message: Message, state: FSMContext) -> None:
    if message.text in REMINDER_BUTTONS | MENU_BUTTONS:
        await message.answer(
            "📅 Введите дату и время или /start для отмены.",
            **HTML,
        )
        return

    remind_at = parse_date_time(message.text)
    if remind_at is None:
        await message.answer(format_invalid_datetime(), **HTML)
        return

    await finish_task_creation(message, state, remind_at)


@router.message(F.text == DELETE_TASK_BTN)
async def btn_delete_task(message: Message, state: FSMContext) -> None:
    tasks = db.get_tasks(get_telegram_user_id(message))

    if not tasks:
        await message.answer(
            format_no_tasks_to_delete(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await state.set_state(TaskStates.waiting_for_task_id)
    await message.answer(
        format_prompt_delete_task(tasks),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_task_id, F.text)
async def process_task_delete(message: Message, state: FSMContext) -> None:
    if message.text in MENU_BUTTONS:
        await message.answer(
            "🔢 Введите номер задачи или /start для отмены.",
            reply_markup=get_main_menu(),
        )
        return

    if not message.text.isdigit():
        await message.answer(
            "⚠️ Введите число — номер задачи из списка.",
            reply_markup=get_main_menu(),
        )
        return

    task_number = int(message.text)
    deleted = db.delete_task(get_telegram_user_id(message), task_number)
    await state.clear()

    if deleted:
        await message.answer(
            format_task_deleted(task_number),
            reply_markup=get_main_menu(),
            **HTML,
        )
    else:
        await message.answer(
            format_task_not_found(task_number),
            reply_markup=get_main_menu(),
            **HTML,
        )


@router.message(Command("clear"))
async def cmd_clear(message: Message, state: FSMContext) -> None:
    user_id = get_telegram_user_id(message)
    count = db.count_tasks(user_id)

    if count == 0:
        await message.answer(
            format_clear_empty(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await state.set_state(TaskStates.waiting_for_clear_confirm)
    await message.answer(
        format_clear_confirm(count),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_clear_confirm, F.text)
async def process_clear_confirm(message: Message, state: FSMContext) -> None:
    if message.text.strip().upper() == "ДА":
        user_id = get_telegram_user_id(message)
        deleted = db.clear_all_tasks(user_id)
        await state.clear()
        await message.answer(
            format_clear_done(deleted),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await state.clear()
    await message.answer(
        format_clear_cancelled(),
        reply_markup=get_main_menu(),
    )


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext, command: CommandObject) -> None:
    if not command.args or not command.args.strip():
        await message.answer(
            "📝 Укажите текст задачи.\nПример: <code>/add Купить молоко</code>",
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    task_text = command.args.strip()
    user_id = get_telegram_user_id(message)
    task_number, task_id = db.add_task(user_id, task_text)
    await start_reminder_setup(message, state, task_number, task_id, task_text)
