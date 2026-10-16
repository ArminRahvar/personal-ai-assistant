
from datetime import timezone
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.database.connection import SessionFactory
from app.database.models import Reminder, User
from app.services.reminder_service import delete_reminder

router = Router()


@router.message(Command("reminders"))
async def list_reminders(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        result = await session.execute(
            select(Reminder)
            .where(
                Reminder.telegram_id == message.from_user.id,
                Reminder.is_sent.is_(False),
            )
            .order_by(Reminder.scheduled_at)
        )
        reminders = list(result.scalars().all())

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )
        user = user_result.scalar_one_or_none()

    if not reminders:
        await message.answer("یادآوریِ در انتظاری ندارید.")
        return

    tz = ZoneInfo(user.timezone if user else "Asia/Tehran")
    lines = ["یادآوری‌های ثبت‌شده:"]

    for reminder in reminders:
        local_time = reminder.scheduled_at.astimezone(tz)
        lines.append(
            f"\nشناسه: {reminder.id}\n"
            f"زمان: {local_time:%Y-%m-%d %H:%M}\n"
            f"متن: {reminder.text}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("delete_reminder"))
async def remove_reminder(message: Message):
    if not message.from_user:
        return

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) != 2:
        await message.answer(
            "برای حذف، شناسه یادآوری را وارد کنید:\n"
            "/delete_reminder شناسه"
        )
        return

    async with SessionFactory() as session:
        deleted = await delete_reminder(
            session=session,
            telegram_id=message.from_user.id,
            reminder_id=parts[1].strip(),
        )

    if deleted:
        await message.answer("یادآوری حذف شد.")
    else:
        await message.answer(
            "یادآوری پیدا نشد؛ ممکن است قبلاً ارسال یا حذف شده باشد."
        )
