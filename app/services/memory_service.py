
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserMemory




async def save_memory(
    session: AsyncSession,
    telegram_id: int,
    content: str,
    category: str = "general",
    importance: int = 3,
) -> UserMemory:
    content = content.strip()

    if not content:
        raise ValueError("Memory content cannot be empty")
    if not 1 <= importance <= 5:
        raise ValueError("Importance must be between 1 and 5")

    result = await session.execute(
        select(UserMemory).where(
            UserMemory.telegram_id == telegram_id,
            UserMemory.content == content,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    memory = UserMemory(
        telegram_id=telegram_id,
        content=content,
        category=category,
        importance=importance,
    )
    session.add(memory)
    await session.flush()

    result = await session.execute(
        select(UserMemory)
        .where(UserMemory.telegram_id == telegram_id)
        .order_by(
            UserMemory.importance.asc(),
            UserMemory.created_at.asc(),
        )
    )
    memories = list(result.scalars().all())

    for old_memory in memories[:-50]:
        await session.delete(old_memory)

    await session.commit()
    await session.refresh(memory)
    return memory


async def list_memories(
    session: AsyncSession,
    telegram_id: int,
) -> list[UserMemory]:
    result = await session.execute(
        select(UserMemory)
        .where(UserMemory.telegram_id == telegram_id)
        .order_by(UserMemory.importance.desc(), UserMemory.created_at.desc()).limit(10)
    )
    return list(result.scalars().all())


async def delete_memory(
    session: AsyncSession,
    telegram_id: int,
    memory_id: str,
) -> bool:
    result = await session.execute(
        select(UserMemory).where(
            UserMemory.id == memory_id,
            UserMemory.telegram_id == telegram_id,
        )
    )
    memory = result.scalar_one_or_none()

    if memory is None:
        return False

    await session.delete(memory)
    await session.commit()
    return True
