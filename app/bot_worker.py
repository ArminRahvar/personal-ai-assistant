import asyncio
import logging

from app.core.config import get_settings


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for the bot worker")

    from app.bot.bot import bot, dp
    from app.database.connection import engine
    from app.services.reminder_scheduler import reminder_scheduler

    polling_task = asyncio.create_task(dp.start_polling(bot))
    scheduler_task = asyncio.create_task(reminder_scheduler())

    try:
        done, _ = await asyncio.wait(
            {polling_task, scheduler_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            task.result()
        raise RuntimeError("A bot worker task stopped unexpectedly")
    finally:
        for task in (polling_task, scheduler_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(
            polling_task,
            scheduler_task,
            return_exceptions=True,
        )
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run())
