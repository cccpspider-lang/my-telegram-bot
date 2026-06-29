import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Создайте файл .env и укажите токен бота.")

SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@dropovod3000")

DATABASE_PATH = BASE_DIR / "tasks.db"
