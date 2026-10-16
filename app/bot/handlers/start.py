
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database.connection import SessionFactory
from app.services.user_service import get_or_create_user

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            language=message.from_user.language_code or "fa",
        )

    await message.answer(
        "سلام! دستیار شخصی شما آماده است.\n"
        f"شناسه کاربری شما: {user.id}"
    )

