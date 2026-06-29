import html
from datetime import datetime

from aiogram.types import Message

from reminders.constants import REPEAT_DISPLAY
from utils.datetime_parser import format_remind_at


def get_user_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "друг"
    return user.first_name or user.full_name or "друг"


def format_welcome(name: str) -> str:
    return (
        f"👋 Привет, <b>{html.escape(name)}</b>!\n\n"
        "Простой бот для задач с напоминаниями 📌\n"
        "Выберите действие в меню 👇"
    )


def format_help() -> str:
    return (
        "ℹ️ <b>Как пользоваться ботом</b>\n\n"
        "<b>📋 Мои задачи</b> — список ваших задач\n\n"
        "<b>➕ Добавить задачу</b>\n"
        "1. Введите текст\n"
        "2. Укажите дату и время: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "3. Выберите периодичность\n\n"
        "<b>🗑 Удалить задачу</b> — выберите номер задачи\n\n"
        "<b>❤️ Поддержка</b> — связаться с автором\n\n"
        "Кнопка «⬅️ Назад» возвращает в главное меню."
    )


def format_support(username: str) -> str:
    return f"По всем вопросам: {html.escape(username)}"


def format_tasks_list(tasks: list) -> str:
    lines = ["📋 <b>Мои задачи</b>\n"]
    for task in tasks:
        repeat_label = REPEAT_DISPLAY.get(task["repeat_type"], task["repeat_type"])
        lines.append(f"<b>{task['task_number']}.</b> {html.escape(task['text'])}")
        if task["remind_at"]:
            lines.append(f"⏰ {_format_remind_at(task['remind_at'])}")
        lines.append(f"🔁 {repeat_label}\n")
    return "\n".join(lines).strip()


def format_empty_tasks() -> str:
    return "📭 <b>Задач пока нет</b>\n\nНажмите «➕ Добавить задачу»."


def format_prompt_add_task() -> str:
    return "➕ <b>Шаг 1 из 3</b>\n\nВведите текст задачи."


def format_prompt_datetime() -> str:
    return (
        "📅 <b>Шаг 2 из 3</b>\n\n"
        "Когда напомнить?\n"
        "Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>30.06.2026 18:30</code>"
    )


def format_prompt_repeat() -> str:
    return "🔁 <b>Шаг 3 из 3</b>\n\nВыберите периодичность:"


def format_invalid_datetime() -> str:
    return (
        "⚠️ Неверный формат.\n\n"
        "Используйте: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>30.06.2026 18:30</code>\n"
        "Дата должна быть в будущем."
    )


def format_task_saved(
    task_number: int,
    text: str,
    remind_at: datetime,
    repeat_type: str,
) -> str:
    repeat_label = REPEAT_DISPLAY.get(repeat_type, repeat_type)
    return (
        "✅ <b>Задача сохранена</b>\n\n"
        f"<b>{task_number}.</b> {html.escape(text)}\n"
        f"⏰ {format_remind_at(remind_at)}\n"
        f"🔁 {repeat_label}"
    )


def format_task_deleted(task_number: int) -> str:
    return f"🗑 Задача <b>#{task_number}</b> удалена."


def format_delete_prompt() -> str:
    return "🗑 <b>Удалить задачу</b>\n\nВыберите номер задачи:"


def format_no_tasks_to_delete() -> str:
    return "📭 <b>Нечего удалять</b>\n\nСписок задач пуст."


def format_back_to_menu() -> str:
    return "↩️ Главное меню."


def _format_remind_at(value: str) -> str:
    try:
        return format_remind_at(datetime.fromisoformat(value))
    except ValueError:
        return value
