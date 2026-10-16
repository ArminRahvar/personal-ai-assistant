from sqlalchemy import select
from datetime import datetime
from app.database.models import Task



async def add_task(
    session,
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

async def list_tasks(session, telegram_id: int) -> list[Task]:
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
    session,
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
    await session.commit()
    return True

async def delete_task(session, telegram_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.telegram_id == telegram_id,
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        return False

    await session.delete(task)
    await session.commit()
    return True


async def list_completed_tasks(session, telegram_id: int) -> list[Task]:
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


