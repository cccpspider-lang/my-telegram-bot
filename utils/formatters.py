import html
from datetime import datetime

from aiogram.types import Message

from utils.datetime_parser import format_remind_at


def get_user_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "друг"
    return user.first_name or user.full_name or "друг"


def format_welcome(name: str) -> str:
    safe_name = html.escape(name)
    return (
        f"👋 Привет, <b>{safe_name}</b>!\n\n"
        "Я помогу управлять твоими задачами 📌\n\n"
        "• ➕ добавлять задачи\n"
        "• 🔔 ставить напоминания\n"
        "• 📋 просматривать список\n"
        "• ❌ удалять задачи\n\n"
        "Выбери действие в меню 👇"
    )


def format_help() -> str:
    return (
        "ℹ️ <b>Справка</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/add &lt;текст&gt; — добавить задачу\n"
        "/tasks — список задач\n"
        "/clear — удалить все задачи\n"
        "/help — эта справка\n\n"
        "<b>Добавление задачи:</b>\n"
        "1. Введите текст задачи\n"
        "2. Выберите напоминание или сохраните без него\n"
        "3. При напоминании укажите дату: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "🔒 Каждый пользователь видит только свои задачи."
    )


def format_support(username: str) -> str:
    return f"По всем вопросам: {html.escape(username)}"


def format_tasks_list(tasks: list) -> str:
    lines = ["📋 <b>Ваши задачи</b>\n"]
    for task in tasks:
        line = f"<b>{task['task_number']}.</b> {html.escape(task['text'])}"
        if task["remind_at"]:
            line += f"\n   ⏰ {_format_remind_at(task['remind_at'])}"
        lines.append(line)
    lines.append(f"\n📊 Всего: <b>{len(tasks)}</b>")
    return "\n".join(lines)


def format_empty_tasks() -> str:
    return (
        "📭 <b>Список пуст</b>\n\n"
        "Нажмите «➕ Добавить задачу» или отправьте:\n"
        "<code>/add Купить молоко</code>"
    )


def format_task_added(task_number: int, text: str, remind_at: datetime | None = None) -> str:
    message = (
        "✅ <b>Задача сохранена</b>\n\n"
        f"🔢 Номер: <b>#{task_number}</b>\n"
        f"📝 Текст: {html.escape(text)}"
    )
    if remind_at:
        message += f"\n⏰ Напоминание: <b>{format_remind_at(remind_at)}</b>"
    else:
        message += "\n🔕 Без напоминания"
    return message


def format_task_deleted(task_number: int) -> str:
    return (
        "🗑 <b>Задача удалена</b>\n\n"
        f"Задача <b>#{task_number}</b> больше не в списке."
    )


def format_task_not_found(task_number: int) -> str:
    return (
        "⚠️ <b>Задача не найдена</b>\n\n"
        f"Задачи с номером <b>#{task_number}</b> нет.\n"
        "Проверьте список: /tasks"
    )


def format_prompt_add_task() -> str:
    return (
        "➕ <b>Новая задача</b>\n\n"
        "Введите текст задачи одним сообщением."
    )


def format_reminder_choice(text: str) -> str:
    return (
        "🔔 <b>Напоминание</b>\n\n"
        f"📝 Задача: {html.escape(text)}\n\n"
        "Добавить напоминание или сохранить задачу без него?"
    )


def format_prompt_datetime() -> str:
    return (
        "📅 <b>Дата и время напоминания</b>\n\n"
        "Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>30.06.2026 18:30</code>"
    )


def format_invalid_datetime() -> str:
    return (
        "⚠️ Неверный формат.\n\n"
        "Используйте: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>30.06.2026 18:30</code>\n"
        "Дата должна быть в будущем."
    )


def format_back_to_menu() -> str:
    return "↩️ Возвращаю в главное меню."


def format_prompt_delete_task(tasks: list) -> str:
    return (
        f"{format_tasks_list(tasks)}\n\n"
        "❌ <b>Удаление задачи</b>\n"
        "Отправьте номер задачи из списка."
    )


def format_no_tasks_to_delete() -> str:
    return "📭 <b>Нечего удалять</b>\n\nСписок задач пуст."


def format_clear_confirm(count: int) -> str:
    return (
        "⚠️ <b>Очистка списка</b>\n\n"
        f"Будет удалено задач: <b>{count}</b>\n\n"
        "Отправьте <b>ДА</b> для подтверждения."
    )


def format_clear_done(count: int) -> str:
    return (
        "🧹 <b>Список очищен</b>\n\n"
        f"Удалено задач: <b>{count}</b>"
    )


def format_clear_cancelled() -> str:
    return "↩️ Очистка отменена."


def format_clear_empty() -> str:
    return "📭 <b>Список уже пуст</b>\n\nУдалять нечего."


def _format_remind_at(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return format_remind_at(dt)
    except ValueError:
        return value
