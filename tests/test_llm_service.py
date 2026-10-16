from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_service import generate_response

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from openai import APIConnectionError

from app.services.llm_service import request_with_retry

@pytest.mark.asyncio
async def test_generate_response_uses_user_history():
    user_message = "سلام"
    telegram_id = 123

    previous_message = MagicMock()
    previous_message.role = "user"
    previous_message.content = "اسم من آرمن است"

    session = AsyncMock()
    session.add_all = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [previous_message]
    session.execute.return_value = result

    response = MagicMock()
    response.choices[0].message.content = "سلام آرمن!"

    with (
        patch("app.services.llm_service.SessionFactory") as factory,
        patch(
            "app.services.llm_service.list_memories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            return_value=response,
        ) as create,
    ):
        factory.return_value.__aenter__ = AsyncMock(return_value=session)
        factory.return_value.__aexit__ = AsyncMock(return_value=False)

        answer = await generate_response(user_message, telegram_id)

    assert answer == "سلام آرمن!"

    messages = create.call_args.kwargs["messages"]
    assert any(
        item["role"] == "user"
        and item["content"] == "اسم من آرمن است"
        for item in messages
    )
    assert messages[-1] == {"role": "user", "content": "سلام"}
    session.commit.assert_awaited_once()






@pytest.mark.asyncio
async def test_request_with_retry_succeeds_on_second_attempt():
    response = MagicMock()
    response.choices[0].message.content = "Hello"

    with (
        patch(
            "app.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            side_effect=[APIConnectionError(request=MagicMock()), response],
        ) as mock_create,
        patch("app.services.llm_service.asyncio.sleep", new_callable=AsyncMock),
    ):
        answer = await request_with_retry([{"role": "user", "content": "Hi"}])

    assert answer == "Hello"
    assert mock_create.await_count == 2


@pytest.mark.asyncio
async def test_request_with_retry_raises_after_three_failures():
    with (
        patch(
            "app.services.llm_service.client.chat.completions.create",
            new_callable=AsyncMock,
            side_effect=APIConnectionError(request=MagicMock()),
        ) as mock_create,
        patch("app.services.llm_service.asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(APIConnectionError):
            await request_with_retry([{"role": "user", "content": "Hi"}])

    assert mock_create.await_count == 3