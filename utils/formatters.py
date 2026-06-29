import html
from datetime import datetime

from aiogram.types import Message

from reminders.constants import REPEAT_LABELS
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
        "• 🔔 создавать напоминания\n"
        "• 📋 показывать списки\n"
        "• ❌ удалять по номеру\n"
        "• 🗑 очищать всё командой /clear\n\n"
        "Выбери действие в меню ниже 👇"
    )


def format_help() -> str:
    return (
        "ℹ️ <b>Справка</b>\n\n"
        "<b>Задачи:</b>\n"
        "/start — главное меню\n"
        "/add &lt;текст&gt; — добавить задачу\n"
        "/tasks — список задач\n"
        "/clear — удалить все задачи\n\n"
        "<b>Напоминания:</b>\n"
        "/reminders — мои напоминания\n"
        "🔔 Напоминания — создать новое\n"
        "📋 Мои напоминания — список\n"
        "🗑 Удалить напоминание — удалить по номеру\n\n"
        "Формат даты: <code>25.06.2026 14:30</code>\n"
        "Периодичность: одноразово, ежедневно, еженедельно, ежемесячно\n\n"
        "/help — эта справка\n\n"
        "🔒 Данные каждого пользователя хранятся отдельно."
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


def format_reminders_list(reminders: list) -> str:
    lines = ["📋 <b>Мои напоминания</b>\n"]
    for reminder in reminders:
        repeat_label = REPEAT_LABELS.get(reminder["repeat_type"], reminder["repeat_type"])
        lines.append(
            f"<b>{reminder['reminder_number']}.</b> {html.escape(reminder['message'])}\n"
            f"   ⏰ {_format_remind_at(reminder['remind_at'])}\n"
            f"   🔁 {repeat_label}"
        )
    lines.append(f"\n📊 Всего: <b>{len(reminders)}</b>")
    return "\n".join(lines)


def format_empty_tasks() -> str:
    return (
        "📭 <b>Список пуст</b>\n\n"
        "У вас пока нет задач.\n"
        "Нажмите «📝 Добавить задачу» или отправьте:\n"
        "<code>/add Купить молоко</code>"
    )


def format_empty_reminders() -> str:
    return (
        "📭 <b>Напоминаний нет</b>\n\n"
        "Создайте первое через кнопку «🔔 Напоминания»."
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


def format_reminder_created(
    reminder_number: int,
    text: str,
    remind_at: datetime,
    repeat_type: str,
) -> str:
    repeat_label = REPEAT_LABELS.get(repeat_type, repeat_type)
    return (
        "✅ <b>Напоминание создано</b>\n\n"
        f"🔢 Номер: <b>#{reminder_number}</b>\n"
        f"📝 Текст: {html.escape(text)}\n"
        f"⏰ Когда: <b>{format_remind_at(remind_at)}</b>\n"
        f"🔁 Период: {repeat_label}"
    )


def format_task_deleted(task_number: int) -> str:
    return (
        "🗑 <b>Задача удалена</b>\n\n"
        f"Задача <b>#{task_number}</b> больше не в списке."
    )


def format_reminder_deleted(reminder_number: int) -> str:
    return (
        "🗑 <b>Напоминание удалено</b>\n\n"
        f"Напоминание <b>#{reminder_number}</b> больше не активно."
    )


def format_task_not_found(task_number: int) -> str:
    return (
        "⚠️ <b>Задача не найдена</b>\n\n"
        f"Задачи с номером <b>#{task_number}</b> нет.\n"
        "Проверьте список: /tasks"
    )


def format_reminder_not_found(reminder_number: int) -> str:
    return (
        "⚠️ <b>Напоминание не найдено</b>\n\n"
        f"Напоминания с номером <b>#{reminder_number}</b> нет.\n"
        "Проверьте список: /reminders"
    )


def format_prompt_add_task() -> str:
    return (
        "📝 <b>Новая задача</b>\n\n"
        "Напишите текст задачи одним сообщением.\n"
        "Отмена: /start"
    )


def format_prompt_add_reminder() -> str:
    return (
        "🔔 <b>Новое напоминание</b>\n\n"
        "Напишите текст напоминания одним сообщением.\n"
        "Отмена: /start"
    )


def format_prompt_reminder_datetime() -> str:
    return (
        "📅 <b>Дата и время</b>\n\n"
        "Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>25.06.2026 14:30</code>\n\n"
        "Отмена: /start"
    )


def format_prompt_reminder_repeat() -> str:
    return (
        "🔁 <b>Периодичность</b>\n\n"
        "Выберите, как часто повторять напоминание."
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


def format_invalid_strict_datetime() -> str:
    return (
        "⚠️ Неверный формат.\n\n"
        "Используйте: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Пример: <code>25.06.2026 14:30</code>"
    )


def format_prompt_delete_task(tasks: list) -> str:
    return (
        f"{format_tasks_list(tasks)}\n\n"
        "❌ <b>Удаление задачи</b>\n"
        "Отправьте номер задачи из списка.\n"
        "Отмена: /start"
    )


def format_prompt_delete_reminder(reminders: list) -> str:
    return (
        f"{format_reminders_list(reminders)}\n\n"
        "🗑 <b>Удаление напоминания</b>\n"
        "Отправьте номер напоминания из списка.\n"
        "Отмена: /start"
    )


def format_no_tasks_to_delete() -> str:
    return "📭 <b>Нечего удалять</b>\n\nСписок задач пуст."


def format_no_reminders_to_delete() -> str:
    return "📭 <b>Нечего удалять</b>\n\nСписок напоминаний пуст."


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


def _format_remind_at(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return format_remind_at(dt)
    except ValueError:
        return value
