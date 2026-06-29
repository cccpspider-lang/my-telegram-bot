from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards import DELETE_TASK_BTN, get_main_menu
from keyboards.task import get_delete_tasks_keyboard
from utils.formatters import (
    format_delete_prompt,
    format_no_tasks_to_delete,
    format_task_deleted,
)

router = Router()
HTML = {"parse_mode": "HTML"}


@router.message(F.text == DELETE_TASK_BTN)
async def btn_delete_task(message: Message, state: FSMContext) -> None:
    await state.clear()
    tasks = db.get_tasks(message.from_user.id)

    if not tasks:
        await message.answer(
            format_no_tasks_to_delete(),
            reply_markup=get_main_menu(),
            **HTML,
        )
        return

    await message.answer(
        format_delete_prompt(),
        reply_markup=get_delete_tasks_keyboard(tasks),
        **HTML,
    )


@router.callback_query(F.data.startswith("delete_task:"))
async def callback_delete_task(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]

    if action == "back":
        await state.clear()
        await callback.message.edit_text("↩️ Главное меню.")
        await callback.message.answer("Выберите действие:", reply_markup=get_main_menu())
        await callback.answer()
        return

    if not action.isdigit():
        await callback.answer("Неверный номер.", show_alert=True)
        return

    task_number = int(action)
    deleted = db.delete_task(callback.from_user.id, task_number)

    if deleted:
        await callback.message.edit_text(
            format_task_deleted(task_number),
            **HTML,
        )
        await callback.message.answer("Выберите действие:", reply_markup=get_main_menu())
        await callback.answer("Удалено")
    else:
        await callback.answer("Задача не найдена.", show_alert=True)
