
from aiogram import Bot, Dispatcher

from app.core.config import get_settings
from app.bot.handlers.start import router as start_router
from app.bot.handlers.timezone import router as timezone_router
from app.bot.handlers.remind import router as remind_router
from app.bot.handlers.reminders import router as reminders_router
from app.bot.handlers.memories import router as memories_router
from app.bot.handlers.chat import router as chat_router
from app.bot.handlers.tasks import router as tasks_router

settings = get_settings()

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(timezone_router)
dp.include_router(remind_router)
dp.include_router(reminders_router)
dp.include_router(memories_router)
dp.include_router(chat_router)
dp.include_router(tasks_router)