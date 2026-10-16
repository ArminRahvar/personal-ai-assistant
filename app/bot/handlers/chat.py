
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

router = Router()
logger = logging.getLogger(__name__)


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
        logger.exception("Natural action handling failed")

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

            logger.info("Memory saved: %s", candidate)

    except Exception:
        logger.exception("Memory extraction or saving failed")

    try:
        answer = await generate_response(
            message.text,
            message.from_user.id,
        )
        await message.answer(answer)

    except Exception:
        logger.exception("Failed to generate assistant response")
        await message.answer(
            "در حال حاضر ارتباط با مدل هوش مصنوعی برقرار نشد. "
            "کمی بعد دوباره تلاش کن."
        )


        if candidate:
            async with SessionFactory() as session:
                await save_memory(
                    session=session,
                    telegram_id=message.from_user.id,
                    content=candidate["content"],
                    category=candidate["category"],
                    importance=candidate["importance"],
                )

            logger.info("Memory saved: %s", candidate)

    except Exception:
        logger.exception("Memory extraction or saving failed")

    try:
        answer = await generate_response(
            message.text,
            message.from_user.id,
        )
        await message.answer(answer)

    except Exception:
        logger.exception("Failed to generate assistant response")
        await message.answer(
            "در حال حاضر ارتباط با مدل هوش مصنوعی برقرار نشد. "
            "کمی بعد دوباره تلاش کن."
        )


@router.message(F.text == "/help")
async def help_handler(message: Message):
    await message.answer(
        "راهنمای دستیار شخصی\n\n"
        "گفت‌وگو:\n"
        "هر پیام متنی بفرست تا با هوش مصنوعی صحبت کنی.\n"
        "/clear_history — پاک‌کردن تاریخچه گفتگو\n\n"
        "حافظه:\n"
        "/remember متن — ذخیره یک حافظه\n"
        "/memories — نمایش حافظه‌ها\n"
        "/forget ID — حذف حافظه\n\n"
        "تسک‌ها:\n"
        "/add_task عنوان — افزودن تسک\n"
        "/add_task YYYY-MM-DD HH:MM عنوان — افزودن تسک زمان‌دار\n"
        "/tasks — نمایش تسک‌های باقی‌مانده\n"
        "/complete_task ID — تکمیل تسک\n"
        "/delete_task ID — حذف تسک\n"
        "/completed_tasks — تسک‌های تکمیل‌شده\n"
        "/today — برنامه امروز\n\n"
        "یادآورها:\n"
        "/remind YYYY-MM-DD HH:MM متن — ساخت یادآور\n"
        "/reminders — نمایش یادآورها\n"
        "/delete_reminder ID — حذف یادآور\n\n"
        "تنظیمات:\n"
        "/timezone — تنظیم منطقه زمانی"
    )