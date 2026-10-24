from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.task_service import add_task_with_reminder


@pytest.mark.asyncio
async def test_add_task_with_reminder_commits_both_records_once():
    session = AsyncMock()
    session.add = MagicMock()
    task = await add_task_with_reminder(
        session,
        telegram_id=123,
        title="  Study  ",
        due_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    assert task.title == "Study"
    session.flush.assert_awaited_once()
    assert session.add.call_count == 2
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(task)


@pytest.mark.asyncio
async def test_add_task_with_reminder_rejects_naive_datetime():
    session = AsyncMock()

    with pytest.raises(ValueError, match="timezone-aware"):
        await add_task_with_reminder(
            session,
            telegram_id=123,
            title="Study",
            due_at=datetime.now(),
        )

    session.add.assert_not_called()
    session.commit.assert_not_awaited()
