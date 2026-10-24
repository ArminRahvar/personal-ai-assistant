
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Reminder


async def create_reminder(
    session: AsyncSession,
    telegram_id: int,
    text: str,
    scheduled_at: datetime,
) -> Reminder:
    if scheduled_at.tzinfo is None:
        raise ValueError("scheduled_at must be timezone-aware")

    if scheduled_at <= datetime.now(timezone.utc):
        raise ValueError("Reminder time must be in the future")

    reminder = Reminder(
        telegram_id=telegram_id,
        text=text,
        scheduled_at=scheduled_at,
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def get_pending_reminders(
    session: AsyncSession,
    telegram_id: int,
) -> list[Reminder]:
    result = await session.execute(
        select(Reminder)
        .where(
            Reminder.telegram_id == telegram_id,
            Reminder.is_sent.is_(False),
        )
        .order_by(Reminder.scheduled_at)
    )
    return list(result.scalars().all())



async def delete_reminder(
    session,
    telegram_id: int,
    reminder_id: str,
) -> bool:
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.telegram_id == telegram_id,
            Reminder.is_sent.is_(False),
        )
    )
    reminder = result.scalar_one_or_none()

    if reminder is None:
        return False

    await session.delete(reminder)
    await session.commit()
    return True
