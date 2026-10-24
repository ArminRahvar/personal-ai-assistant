
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    language: str = "fa",
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    user = User(
        telegram_id=telegram_id,
        language=language,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def update_user_timezone(
    session: AsyncSession,
    telegram_id: int,
    timezone: str,
) -> bool:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return False

    user.timezone = timezone
    await session.commit()
    return True


async def set_user_memory_enabled(
    session: AsyncSession,
    telegram_id: int,
    enabled: bool,
) -> bool:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return False

    user.memory_enabled = enabled
    await session.commit()
    return True


async def get_user_memory_enabled(
    session: AsyncSession,
    telegram_id: int,
) -> bool:
    result = await session.execute(
        select(User.memory_enabled).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none() is True
