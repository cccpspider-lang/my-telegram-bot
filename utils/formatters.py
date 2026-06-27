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
        "Я твой помощник по задачам 📌\n\n"
        "Что умею:\n"
        "• 📝 добавлять задачи\n"
        "• ⏰ напоминать в нужное время\n"
        "• 📋 показывать список\n"
        "• ❌ удалять по номеру\n"
        "• 🗑 очищать всё командой /clear\n\n"
        "Выбери действие в меню ниже 👇"
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
        "<b>Кнопки меню:</b>\n"
        "📝 Добавить задачу — ввод новой задачи\n"
        "📋 Мои задачи — ваш личный список\n"
        "❌ Удалить задачу — удаление по номеру\n"
        "ℹ️ Помощь — показать справку\n\n"
        "<b>Напоминания:</b>\n"
        "После добавления задачи можно указать время или дату.\n"
        "Форматы: <code>14:30</code> или <code>25.06.2026 14:30</code>\n\n"
        "🔒 Задачи хранятся отдельно для каждого пользователя."
    )


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
        "У вас пока нет задач.\n"
        "Нажмите «📝 Добавить задачу» или отправьте:\n"
        "<code>/add Купить молоко</code>"
    )


def format_task_added(task_number: int, text: str, remind_at: datetime | None = None) -> str:
    message = (
        "✅ <b>Задача добавлена</b>\n\n"
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
        "📝 <b>Новая задача</b>\n\n"
        "Напишите текст задачи одним сообщением.\n"
        "Отмена: /start"
    )


def format_reminder_choice(task_number: int, text: str) -> str:
    return (
        "⏰ <b>Когда напомнить?</b>\n\n"
        f"📝 Задача #{task_number}: {html.escape(text)}\n\n"
        "🕐 <b>Только время</b> — сегодня или завтра\n"
        "📅 <b>Дата и время</b> — точная дата\n"
        "⏭ <b>Без напоминания</b> — сохранить без уведомления"
    )


def format_prompt_time() -> str:
    return (
        "🕐 <b>Укажите время</b>\n\n"
        "Формат: <code>14:30</code>\n"
        "Если время уже прошло, напомню завтра.\n"
        "Отмена: /start"
    )


def format_prompt_datetime() -> str:
    return (
        "📅 <b>Укажите дату и время</b>\n\n"
        "Форматы:\n"
        "• <code>25.06.2026 14:30</code>\n"
        "• <code>25.06 14:30</code> (текущий год)\n\n"
        "Отмена: /start"
    )


def format_invalid_time() -> str:
    return (
        "⚠️ Неверный формат времени.\n\n"
        "Пример: <code>09:00</code> или <code>18:45</code>"
    )


def format_invalid_datetime() -> str:
    return (
        "⚠️ Неверная дата или время.\n\n"
        "Пример: <code>25.06.2026 14:30</code>\n"
        "Дата должна быть в будущем."
    )


def format_prompt_delete_task(tasks: list) -> str:
    return (
        f"{format_tasks_list(tasks)}\n\n"
        "❌ <b>Удаление задачи</b>\n"
        "Отправьте номер задачи из списка.\n"
        "Отмена: /start"
    )


def format_no_tasks_to_delete() -> str:
    return "📭 <b>Нечего удалять</b>\n\nСписок задач пуст."


def format_clear_confirm(count: int) -> str:
    return (
        "⚠️ <b>Очистка списка</b>\n\n"
        f"Будет удалено задач: <b>{count}</b>\n\n"
        "Отправьте <b>ДА</b> для подтверждения или /start для отмены."
    )


def format_clear_done(count: int) -> str:
    return (
        "🧹 <b>Список очищен</b>\n\n"
        f"Удалено задач: <b>{count}</b>\n"
        "Можно начать с чистого листа ✨"
    )


def format_clear_cancelled() -> str:
    return "↩️ Очистка отменена."


def format_clear_empty() -> str:
    return "📭 <b>Список уже пуст</b>\n\nУдалять нечего."


def format_reminder_notification(task_text: str) -> str:
    return (
        "⏰ <b>Пора выполнить задачу!</b>\n\n"
        f"📝 {html.escape(task_text)}"
    )


def _format_remind_at(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return format_remind_at(dt)
    except ValueError:
        return value
