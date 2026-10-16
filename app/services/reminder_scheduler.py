
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.bot.bot import bot
from app.database.connection import SessionFactory
from app.database.models import Reminder

logger = logging.getLogger(__name__)


async def process_reminders():
    async with SessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(Reminder)
                .where(
                    Reminder.is_sent.is_(False),
                    Reminder.scheduled_at <= datetime.now(timezone.utc),
                )
                .order_by(Reminder.scheduled_at)
                .with_for_update(skip_locked=True)
                .limit(50)
            )
            reminders = list(result.scalars().all())

            for reminder in reminders:
                try:
                    await bot.send_message(
                        chat_id=reminder.telegram_id,
                        text=f"⏰ یادآوری:\n{reminder.text}",
                    )
                    reminder.is_sent = True
                except Exception:
                    logger.exception(
                        "Failed to send reminder %s", reminder.id
                    )


async def reminder_scheduler():
    while True:
        try:
            await process_reminders()
        except Exception:
            logger.exception("Reminder scheduler failed")

        await asyncio.sleep(10)
