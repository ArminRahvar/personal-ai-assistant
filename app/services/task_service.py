from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Task, Reminder


async def add_task(
    session: AsyncSession,
    telegram_id: int,
    title: str,
    due_at: datetime | None = None,
) -> Task:
    title = title.strip()

    if not title:
        raise ValueError("Task title cannot be empty")

    task = Task(
        telegram_id=telegram_id,
        title=title,
        due_at=due_at,
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


async def add_task_with_reminder(
    session: AsyncSession,
    telegram_id: int,
    title: str,
    due_at: datetime,
) -> Task:
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty")
    if due_at.tzinfo is None:
        raise ValueError("Task due time must be timezone-aware")
    if due_at <= datetime.now(timezone.utc):
        raise ValueError("Task due time must be in the future")

    task = Task(
        telegram_id=telegram_id,
        title=title,
        due_at=due_at,
    )
    session.add(task)
    await session.flush()
    session.add(
        Reminder(
            telegram_id=telegram_id,
            task_id=task.id,
            text=f"موعد انجام تسک: {title}",
            scheduled_at=due_at,
        )
    )
    await session.commit()
    await session.refresh(task)
    return task


async def list_tasks(
    session: AsyncSession,
    telegram_id: int,
) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(
            Task.telegram_id == telegram_id,
            Task.is_completed.is_(False),
        )
        .order_by(Task.id.desc())
    )

    return list(result.scalars().all())


async def complete_task(
    session: AsyncSession,
    telegram_id: int,
    task_id: int,
) -> bool:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.telegram_id == telegram_id,
        )
    )

    task = result.scalar_one_or_none()

    if task is None or task.is_completed:
        return False

    task.is_completed = True

    # حذف یادآورهای ارسال‌نشده‌ی وابسته به تسک
    await session.execute(
        delete(Reminder).where(
            Reminder.task_id == task_id,
            Reminder.telegram_id == telegram_id,
            Reminder.is_sent.is_(False),
        )
    )

    await session.commit()
    return True


async def delete_task(
    session: AsyncSession,
    telegram_id: int,
    task_id: int,
) -> bool:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.telegram_id == telegram_id,
        )
    )

    task = result.scalar_one_or_none()

    if task is None:
        return False

    # حذف یادآورهای ارسال‌نشده‌ی وابسته به تسک
    await session.execute(
        delete(Reminder).where(
            Reminder.task_id == task_id,
            Reminder.telegram_id == telegram_id,
            Reminder.is_sent.is_(False),
        )
    )

    await session.delete(task)
    await session.commit()

    return True


async def list_completed_tasks(
    session: AsyncSession,
    telegram_id: int,
) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(
            Task.telegram_id == telegram_id,
            Task.is_completed.is_(True),
        )
        .order_by(Task.id.desc())
        .limit(20)
    )

    return list(result.scalars().all())


async def list_overdue_tasks(
    session: AsyncSession,
    telegram_id: int,
    now: datetime,
) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(
            Task.telegram_id == telegram_id,
            Task.is_completed.is_(False),
            Task.due_at.is_not(None),
            Task.due_at < now,
        )
        .order_by(Task.due_at.asc())
    )

    return list(result.scalars().all())


async def update_task(
    session: AsyncSession,
    telegram_id: int,
    task_id: int,
    title: str | None = None,
    due_at: datetime | None = None,
) -> Task | None:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.telegram_id == telegram_id,
        )
    )

    task = result.scalar_one_or_none()

    if task is None:
        return None

    if title is not None:
        title = title.strip()

        if not title:
            raise ValueError("Task title cannot be empty")

        task.title = title

    if due_at is not None:
        task.due_at = due_at
        await session.execute(
            delete(Reminder).where(
                Reminder.task_id == task_id,
                Reminder.telegram_id == telegram_id,
                Reminder.is_sent.is_(False),
            )
        )
        if due_at > datetime.now(timezone.utc):
            session.add(
                Reminder(
                    telegram_id=telegram_id,
                    task_id=task_id,
                    text=f"موعد انجام تسک: {task.title}",
                    scheduled_at=due_at,
                )
            )

    await session.commit()
    await session.refresh(task)

    return task