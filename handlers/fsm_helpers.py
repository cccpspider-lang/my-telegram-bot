import logging

from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


async def get_state_data(state: FSMContext) -> dict:
    """Возвращает данные FSM-состояния."""
    return await state.get_data()


def require_keys(data: dict, *keys: str) -> bool:
    """Проверяет наличие обязательных ключей в данных FSM."""
    missing = [key for key in keys if key not in data]
    if missing:
        logger.error("FSM data missing keys: %s | data=%s", missing, data)
        return False
    return True
