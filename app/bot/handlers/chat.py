
import logging

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import delete

from app.services.llm_service import generate_response
from app.services.memory_extractor import extract_memory
from app.services.memory_service import save_memory
from app.database.connection import SessionFactory
from app.database.models import ConversationMessage
from app.services.natural_actions import handle_natural_action
from app.services.user_service import get_user_memory_enabled

router = Router()
logger = logging.getLogger(__name__)
TELEGRAM_MESSAGE_LIMIT = 4096


def split_telegram_message(
    text: str,
    max_length: int = TELEGRAM_MESSAGE_LIMIT,
) -> list[str]:
    if max_length < 1:
        raise ValueError("max_length must be positive")

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_length, len(text))
        if end < len(text):
            newline = text.rfind("\n", start, end)
            space = text.rfind(" ", start, end)
            boundary = max(newline, space)
            if boundary > start + max_length // 2:
                end = boundary + 1

        chunks.append(text[start:end])
        start = end

    return chunks


@router.message(F.text == "/clear_history")
async def clear_history_handler(message: Message):
    try:
        async with SessionFactory() as session:
            await session.execute(
                delete(ConversationMessage).where(
                    ConversationMessage.telegram_id == message.from_user.id
                )
            )
            await session.commit()

        await message.answer(
            "تاریخچه مکالمه پاک شد. حافظه‌های بلندمدت و یادآورها دست‌نخورده باقی ماندند."
        )

    except Exception:
        logger.exception("Failed to clear conversation history")
        await message.answer("پاک‌کردن تاریخچه با خطا مواجه شد.")



@router.message(F.text & ~F.text.startswith("/"))
async def chat_handler(message: Message):
    try:
        action_result = await handle_natural_action(
            message.text,
            message.from_user.id,
        )

        if action_result is not None:
            await message.answer(action_result)
            return

    except Exception:
        logger.exception("Failed to save the requested task or reminder")
        await message.answer(
            "ثبت تسک یا یادآور با خطا مواجه شد. لطفاً کمی بعد دوباره تلاش کن."
        )
        return

    try:
        async with SessionFactory() as session:
            memory_enabled = await get_user_memory_enabled(
                session,
                message.from_user.id,
            )
    except Exception:
        logger.exception("Failed to read memory preference")
        memory_enabled = False

    if memory_enabled:
        try:
            candidate = await extract_memory(message.text)
            if candidate:
                async with SessionFactory() as session:
                    await save_memory(
                        session=session,
                        telegram_id=message.from_user.id,
                        content=candidate["content"],
                        category=candidate["category"],
                        importance=candidate["importance"],
                    )

                logger.info(
                    "Memory saved for user %s (category=%s, importance=%s)",
                    message.from_user.id,
                    candidate["category"],
                    candidate["importance"],
                )

        except Exception:
            logger.exception("Memory extraction or saving failed")

    try:
        answer = await generate_response(
            message.text,
            message.from_user.id,
        )
    except Exception:
        logger.exception("Failed to generate assistant response")
        await message.answer(
            "در حال حاضر ارتباط با مدل هوش مصنوعی برقرار نشد. "
            "کمی بعد دوباره تلاش کن."
        )
        return

    try:
        for chunk in split_telegram_message(answer):
            await message.answer(chunk)
    except Exception:
        logger.exception("Failed to send assistant response through Telegram")
        await message.answer(
            "پاسخ آماده شد اما ارسال آن در تلگرام با خطا مواجه شد."
        )
