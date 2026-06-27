from reminders.service import ReminderService

_reminder_service: ReminderService | None = None


def set_reminder_service(service: ReminderService) -> None:
    global _reminder_service
    _reminder_service = service


def get_reminder_service() -> ReminderService:
    if _reminder_service is None:
        raise RuntimeError("ReminderService не инициализирован")
    return _reminder_service
