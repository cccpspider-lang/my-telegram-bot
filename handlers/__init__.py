from aiogram import Router

from handlers.commands import router as commands_router
from handlers.reminders import router as reminders_router

router = Router()
router.include_router(commands_router)
router.include_router(reminders_router)
