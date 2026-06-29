from aiogram import F, Router
from aiogram.filters import Command, CommandObject
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
from keyboards.reminder import (
    ADD_REMINDER_BTN,
    SKIP_REMINDER_BTN,
    TASK_REMINDER_BUTTONS,
    get_task_reminder_choice_keyboard,
)
from services.context import get_reminder_service
from utils.datetime_parser import parse_strict_date_time
from utils.formatters import (
    format_back_to_menu,
    format_clear_cancelled,
    format_clear_confirm,
    format_clear_done,
    format_clear_empty,
    format_empty_tasks,
    format_help,
    format_invalid_datetime,
    format_no_tasks_to_delete,
    format_prompt_add_task,
    format_prompt_datetime,
    format_prompt_delete_task,
    format_reminder_choice,
    format_support,
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


async def return_to_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        format_back_to_menu(),
        reply_markup=get_main_menu(),
    )


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


async def save_task_without_reminder(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_text = data["task_text"]
    user_id = get_telegram_user_id(message)
    task_number, _ = db.add_task(user_id, task_text)
    await state.clear()
    await message.answer(
        format_task_added(task_number, task_text),
        reply_markup=get_main_menu(),
        **HTML,
    )


async def save_task_with_reminder(
    message: Message,
    state: FSMContext,
    remind_at,
) -> None:
    data = await state.get_data()
    task_text = data["task_text"]
    user_id = get_telegram_user_id(message)
    task_number, task_id = db.add_task(user_id, task_text)
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
    await message.answer(
        format_welcome(get_user_name(message)),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(Command("help"))
@router.message(F.text == HELP_BTN)
async def cmd_help(message: Message) -> None:
    await show_help(message)


@router.message(F.text == SUPPORT_BTN)
async def btn_support(message: Message) -> None:
    await message.answer(
        format_support(SUPPORT_USERNAME),
        reply_markup=get_main_menu(),
        **HTML,
    )


@router.message(Command("tasks"))
@router.message(F.text == MY_TASKS_BTN)
async def cmd_tasks(message: Message) -> None:
    await show_tasks(message)


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
        await return_to_main_menu(message, state)
        return

    if message.text in MENU_BUTTONS:
        await message.answer(
            "✏️ Введите текст задачи или нажмите «⬅️ Назад».",
            reply_markup=get_back_keyboard(),
        )
        return

    task_text = message.text.strip()
    if not task_text:
        await message.answer(
            "⚠️ Текст не может быть пустым. Попробуйте ещё раз:",
            reply_markup=get_back_keyboard(),
        )
        return

    await state.update_data(task_text=task_text)
    await state.set_state(TaskStates.waiting_for_reminder_choice)
    await message.answer(
        format_reminder_choice(task_text),
        reply_markup=get_task_reminder_choice_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_reminder_choice, F.text)
async def process_reminder_choice(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await return_to_main_menu(message, state)
        return

    if message.text == SKIP_REMINDER_BTN:
        await save_task_without_reminder(message, state)
        return

    if message.text == ADD_REMINDER_BTN:
        await state.set_state(TaskStates.waiting_for_datetime)
        await message.answer(
            format_prompt_datetime(),
            reply_markup=get_back_keyboard(),
            **HTML,
        )
        return

    await message.answer(
        "Выберите действие из меню.",
        reply_markup=get_task_reminder_choice_keyboard(),
    )


@router.message(TaskStates.waiting_for_datetime, F.text)
async def process_reminder_datetime(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await return_to_main_menu(message, state)
        return

    if message.text in TASK_REMINDER_BUTTONS | MENU_BUTTONS:
        await message.answer(
            "📅 Введите дату и время или нажмите «⬅️ Назад».",
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

    await save_task_with_reminder(message, state, remind_at)


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
        reply_markup=get_back_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_task_id, F.text)
async def process_task_delete(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await return_to_main_menu(message, state)
        return

    if message.text in MENU_BUTTONS:
        await message.answer(
            "🔢 Введите номер задачи или нажмите «⬅️ Назад».",
            reply_markup=get_back_keyboard(),
        )
        return

    if not message.text.isdigit():
        await message.answer(
            "⚠️ Введите число — номер задачи из списка.",
            reply_markup=get_back_keyboard(),
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
        reply_markup=get_back_keyboard(),
        **HTML,
    )


@router.message(TaskStates.waiting_for_clear_confirm, F.text)
async def process_clear_confirm(message: Message, state: FSMContext) -> None:
    if message.text == BACK_BTN:
        await return_to_main_menu(message, state)
        return

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
            "➕ Укажите текст задачи.\nПример: <code>/add Купить молоко</code>",
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    task_text = command.args.strip()
    await state.update_data(task_text=task_text)
    await state.set_state(TaskStates.waiting_for_reminder_choice)
    await message.answer(
        format_reminder_choice(task_text),
        reply_markup=get_task_reminder_choice_keyboard(),
        **HTML,
    )
