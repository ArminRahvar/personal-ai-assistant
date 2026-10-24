from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.bot.handlers.chat import chat_handler, split_telegram_message


def make_message():
    message = MagicMock()
    message.text = "سلام"
    message.from_user.id = 123
    message.answer = AsyncMock()
    return message


def test_split_telegram_message_respects_limit_and_preserves_text():
    text = ("پاسخ بلند " * 1000) + "\nپایان"

    chunks = split_telegram_message(text, max_length=1000)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert "".join(chunks) == text


def test_split_telegram_message_keeps_short_text_in_one_chunk():
    assert split_telegram_message("سلام") == ["سلام"]


def test_split_telegram_message_rejects_invalid_limit():
    with pytest.raises(ValueError, match="positive"):
        split_telegram_message("test", max_length=0)


@pytest.mark.asyncio
async def test_chat_handler_skips_memory_extraction_when_disabled():
    message = make_message()

    with (
        patch(
            "app.bot.handlers.chat.handle_natural_action",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.bot.handlers.chat.get_user_memory_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "app.bot.handlers.chat.extract_memory",
            new_callable=AsyncMock,
        ) as extract,
        patch(
            "app.bot.handlers.chat.generate_response",
            new_callable=AsyncMock,
            return_value="سلام!",
        ) as generate,
    ):
        await chat_handler(message)

    generate.assert_awaited_once_with("سلام", 123)
    extract.assert_not_awaited()
    message.answer.assert_awaited_once_with("سلام!")


@pytest.mark.asyncio
async def test_chat_handler_does_not_save_memory_twice_when_response_fails():
    message = make_message()
    candidate = {
        "content": "Likes tea",
        "category": "preference",
        "importance": 3,
    }
    session = MagicMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "app.bot.handlers.chat.handle_natural_action",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.bot.handlers.chat.get_user_memory_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.bot.handlers.chat.extract_memory",
            new_callable=AsyncMock,
            return_value=candidate,
        ),
        patch(
            "app.bot.handlers.chat.SessionFactory",
            return_value=session_context,
        ),
        patch(
            "app.bot.handlers.chat.save_memory",
            new_callable=AsyncMock,
        ) as save_memory,
        patch(
            "app.bot.handlers.chat.generate_response",
            new_callable=AsyncMock,
            side_effect=RuntimeError("model unavailable"),
        ) as generate,
    ):
        await chat_handler(message)

    save_memory.assert_awaited_once()
    generate.assert_awaited_once_with("سلام", 123)
    message.answer.assert_awaited_once()
    assert "ارتباط با مدل" in message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_chat_handler_splits_long_assistant_response():
    message = make_message()
    answer = "پاسخ " * 1000

    with (
        patch(
            "app.bot.handlers.chat.handle_natural_action",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.bot.handlers.chat.get_user_memory_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "app.bot.handlers.chat.generate_response",
            new_callable=AsyncMock,
            return_value=answer,
        ),
    ):
        await chat_handler(message)

    chunks = [call.args[0] for call in message.answer.await_args_list]
    assert len(chunks) > 1
    assert all(len(chunk) <= 4096 for chunk in chunks)
    assert "".join(chunks) == answer
