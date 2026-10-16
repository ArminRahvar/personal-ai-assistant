
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.connection import SessionFactory
from app.services.user_service import update_user_timezone

router = Router()


@router.message(Command("timezone"))
async def timezone_handler(message: Message):
    if not message.from_user:
        return

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) != 2:
        await message.answer(
            "منطقه زمانی را وارد کنید.\n"
            "مثال: /timezone Asia/Tehran"
        )
        return

    timezone = parts[1].strip()

    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        await message.answer(
            "منطقه زمانی معتبر نیست. مثال: Europe/London"
        )
        return

    async with SessionFactory() as session:
        updated = await update_user_timezone(
            session=session,
            telegram_id=message.from_user.id,
            timezone=timezone,
        )

    if updated:
        await message.answer(f"منطقه زمانی شما به {timezone} تغییر کرد.")
    else:
        await message.answer("ابتدا دستور /start را اجرا کنید.")
