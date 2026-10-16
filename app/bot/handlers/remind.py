
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.connection import SessionFactory
from app.database.models import User
from app.services.reminder_service import create_reminder
from sqlalchemy import select

router = Router()


@router.message(Command("remind"))
async def remind_handler(message: Message):
    if not message.from_user:
        return

    parts = (message.text or "").split(maxsplit=3)

    if len(parts) != 4:
        await message.answer(
            "فرمت دستور:\n"
            "/remind YYYY-MM-DD HH:MM متن یادآوری\n\n"
            "مثال:\n"
            "/remind 2026-10-17 09:30 خرید نان"
        )
        return

    _, date_str, time_str, reminder_text = parts

    async with SessionFactory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("ابتدا /start را اجرا کنید.")
            return

        try:
            timezone = ZoneInfo(user.timezone)
            local_time = datetime.strptime(
                f"{date_str} {time_str}",
                "%Y-%m-%d %H:%M",
            ).replace(tzinfo=timezone)

            await create_reminder(
                session=session,
                telegram_id=message.from_user.id,
                text=reminder_text,
                scheduled_at=local_time,
            )
        except ValueError:
            await message.answer(
                "تاریخ، ساعت یا منطقه زمانی معتبر نیست؛ "
                "همچنین زمان باید در آینده باشد."
            )
            return

    await message.answer("یادآوری با موفقیت ذخیره شد.")
