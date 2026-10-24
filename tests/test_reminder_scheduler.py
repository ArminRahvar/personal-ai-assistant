from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.services.reminder_scheduler import process_reminders


@pytest.mark.asyncio
async def test_process_reminders_marks_successful_delivery():
    reminder_id = uuid4()
    claimed_at = datetime.now(timezone.utc)
    reminder = (reminder_id, 123, "Call home", 1, claimed_at)

    with (
        patch(
            "app.services.reminder_scheduler.claim_due_reminders",
            new_callable=AsyncMock,
            return_value=[reminder],
        ),
        patch(
            "app.services.reminder_scheduler.bot.send_message",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.reminder_scheduler.finish_reminder",
            new_callable=AsyncMock,
        ) as finish,
    ):
        await process_reminders()

    finish.assert_awaited_once_with(
        reminder_id,
        claimed_at,
        1,
        sent=True,
    )


@pytest.mark.asyncio
async def test_process_reminders_schedules_retry_after_send_failure():
    reminder_id = uuid4()
    claimed_at = datetime.now(timezone.utc)
    reminder = (reminder_id, 123, "Call home", 2, claimed_at)

    with (
        patch(
            "app.services.reminder_scheduler.claim_due_reminders",
            new_callable=AsyncMock,
            return_value=[reminder],
        ),
        patch(
            "app.services.reminder_scheduler.bot.send_message",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Telegram unavailable"),
        ),
        patch(
            "app.services.reminder_scheduler.finish_reminder",
            new_callable=AsyncMock,
        ) as finish,
    ):
        await process_reminders()

    finish.assert_awaited_once_with(
        reminder_id,
        claimed_at,
        2,
        sent=False,
    )
