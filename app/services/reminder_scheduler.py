
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, update

from app.bot.bot import bot
from app.database.connection import SessionFactory
from app.database.models import Reminder

logger = logging.getLogger(__name__)

CLAIM_LEASE = timedelta(minutes=5)
MAX_RETRY_DELAY = 3600


async def claim_due_reminders() -> list[tuple[UUID, int, str, int, datetime]]:
    now = datetime.now(timezone.utc)
    lease_expiry = now - CLAIM_LEASE
    async with SessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(Reminder)
                .where(
                    Reminder.is_sent.is_(False),
                    Reminder.scheduled_at <= datetime.now(timezone.utc),
                    func.coalesce(
                        Reminder.next_attempt_at,
                        Reminder.scheduled_at,
                    ) <= now,
                    (
                        Reminder.claimed_at.is_(None)
                        | (Reminder.claimed_at < lease_expiry)
                    ),
                )
                .order_by(Reminder.scheduled_at)
                .with_for_update(skip_locked=True)
                .limit(50)
            )
            reminders = list(result.scalars().all())
            claimed = []

            for reminder in reminders:
                reminder.claimed_at = now
                reminder.attempt_count += 1
                claimed.append(
                    (
                        reminder.id,
                        reminder.telegram_id,
                        reminder.text,
                        reminder.attempt_count,
                        now,
                    )
                )

    return claimed


async def finish_reminder(
    reminder_id: UUID,
    claimed_at: datetime,
    attempt_count: int,
    sent: bool,
) -> None:
    async with SessionFactory() as session:
        async with session.begin():
            values: dict[str, bool | datetime | None] = {
                "claimed_at": None,
                "is_sent": sent,
                "next_attempt_at": None,
            }
            if not sent:
                delay = min(
                    MAX_RETRY_DELAY,
                    30 * 2 ** min(attempt_count - 1, 7),
                )
                values["next_attempt_at"] = (
                    datetime.now(timezone.utc) + timedelta(seconds=delay)
                )

            await session.execute(
                update(Reminder)
                .where(
                    Reminder.id == reminder_id,
                    Reminder.is_sent.is_(False),
                    Reminder.claimed_at == claimed_at,
                )
                .values(**values)
            )


async def process_reminders() -> None:
    reminders = await claim_due_reminders()
    for reminder_id, telegram_id, text, attempt_count, claimed_at in reminders:
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=f"⏰ یادآوری:\n{text}",
            )
        except Exception:
            logger.exception("Failed to send reminder %s", reminder_id)
            await finish_reminder(
                reminder_id,
                claimed_at,
                attempt_count,
                sent=False,
            )
        else:
            await finish_reminder(
                reminder_id,
                claimed_at,
                attempt_count,
                sent=True,
            )


async def reminder_scheduler():
    while True:
        try:
            await process_reminders()
        except Exception:
            logger.exception("Reminder scheduler failed")

        await asyncio.sleep(10)
