from aiogram import Router

from handlers.callbacks import router as callbacks_router
from handlers.commands import router as commands_router

router = Router()
router.include_router(commands_router)
router.include_router(callbacks_router)
