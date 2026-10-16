
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.memory_service import save_memory
from app.services.memory_service import list_memories, delete_memory

@pytest.mark.asyncio
async def test_save_memory_rejects_empty_content():
    session = AsyncMock()

    with pytest.raises(ValueError, match="empty"):
        await save_memory(
            session=session,
            telegram_id=123,
            content="   ",
        )


@pytest.mark.asyncio
async def test_save_memory_rejects_invalid_importance():
    session = AsyncMock()

    with pytest.raises(ValueError, match="Importance"):
        await save_memory(
            session=session,
            telegram_id=123,
            content="Likes programming",
            importance=6,
        )


@pytest.mark.asyncio
async def test_save_memory_returns_existing_duplicate():
    session = AsyncMock()
    existing_memory = MagicMock()
    existing_memory.content = "I love programming"

    result = MagicMock()
    result.scalar_one_or_none.return_value = existing_memory
    session.execute.return_value = result

    memory = await save_memory(
        session=session,
        telegram_id=123,
        content="I love programming",
    )

    assert memory is existing_memory
    session.add.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_list_memories_returns_user_memories():
    session = AsyncMock()
    memories = [MagicMock(), MagicMock()]

    result = MagicMock()
    result.scalars.return_value.all.return_value = memories
    session.execute.return_value = result

    returned = await list_memories(session, telegram_id=123)

    assert returned == memories


@pytest.mark.asyncio
async def test_delete_memory_returns_false_when_not_found():
    session = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    deleted = await delete_memory(
        session=session,
        telegram_id=123,
        memory_id=999,
    )

    assert deleted is False
    session.commit.assert_not_called()