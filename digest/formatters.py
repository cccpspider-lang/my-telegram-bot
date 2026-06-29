"""Форматирование утреннего плана дня."""


def _task_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "задача"
    if 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        return "задачи"
    return "задач"


def format_morning_plan(
    name: str,
    tasks: list,
    total_today: int,
    completed_yesterday: int,
    streak: int,
) -> str:
    if not tasks:
        return (
            f"🌅 Доброе утро, {name}!\n\n"
            "Сегодня у тебя нет запланированных задач.\n"
            "Самое время поставить новые цели и сделать этот день продуктивным 🚀"
        )

    lines = [
        f"🌅 Доброе утро, {name}!",
        "",
        "Сегодня у тебя:",
    ]
    for task in tasks:
        lines.append(task["text"])

    lines.extend(
        [
            "",
            f"📋 Всего задач на сегодня: {total_today}",
            f"🔥 Серия продуктивности: {streak} дней",
            f"✅ Выполнено вчера: {completed_yesterday} {_task_word(completed_yesterday)}",
            "",
            "🚀 Удачного и продуктивного дня!",
        ]
    )
    return "\n".join(lines)
