from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import logging

from sqlalchemy import select
from app.database.models import User, Task, Reminder
from app.database.connection import SessionFactory
from app.services.task_service import (
    add_task,
    add_task_with_reminder,
    list_tasks,
    complete_task,
    delete_task,
    list_completed_tasks,
    list_overdue_tasks,
    update_task,
)



router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text.startswith("/add_task"))
async def add_task_handler(message: Message):
    parts = message.text.split(maxsplit=3)
    telegram_id = message.from_user.id

    if len(parts) < 2:
        await message.answer(
            "مثال:\n"
            "/add_task یادگیری SQL\n"
            "/add_task 2026-10-17 18:30 یادگیری SQL"
        )
        return

    due_at = None
    title = message.text.split(maxsplit=1)[1]

    if (
        len(parts) == 4
        and "-" in parts[1]
        and ":" in parts[2]
    ):
        try:
            async with SessionFactory() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()

                if user is None:
                    await message.answer("ابتدا دستور /start رو اجرا کن.")
                    return

                timezone = ZoneInfo(user.timezone)
                due_at = datetime.strptime(
                    f"{parts[1]} {parts[2]}",
                    "%Y-%m-%d %H:%M",
                ).replace(tzinfo=timezone)

                if due_at <= datetime.now(timezone):
                    await message.answer("موعد تسک باید در آینده باشه.")
                    return

                title = parts[3].strip()

                if not title:
                    await message.answer("عنوان تسک رو وارد کن.")
                    return

                task = await add_task_with_reminder(
                    session,
                    telegram_id,
                    title,
                    due_at,
                )

        except (ValueError, KeyError):
            await message.answer(
                "تاریخ یا ساعت معتبر نیست. مثال:\n"
                "/add_task 2026-10-17 18:30 یادگیری SQL"
            )
            return

        await message.answer(
            f"تسک ثبت شد: {task.title}\n"
            f"موعد: {due_at.strftime('%Y-%m-%d %H:%M')}\n"
            "یادآور هم تنظیم شد."
        )
        return

    async with SessionFactory() as session:
        task = await add_task(session, telegram_id, title)

    await message.answer(f"تسک ثبت شد: {task.title} (ID: {task.id})")


@router.message(F.text == "/tasks")
async def list_tasks_handler(message: Message):
    async with SessionFactory() as session:
        tasks = await list_tasks(session, message.from_user.id)

    if not tasks:
        await message.answer("هیچ کار انجام‌نشده‌ای نداری.")
        return

    text = "\n".join(
        f"{index}. {task.title} (ID: {task.id})"
        for index, task in enumerate(tasks, start=1)
    )
    await message.answer(f"کارهای باقی‌مانده:\n\n{text}")


@router.message(F.text.startswith("/complete_task"))
async def complete_task_handler(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(
            "شناسه کار رو وارد کن.\nمثال:\n/complete_task 3"
        )
        return

    async with SessionFactory() as session:
        completed = await complete_task(
            session,
            message.from_user.id,
            int(parts[1]),
        )

    if completed:
        await message.answer("کار با موفقیت تکمیل شد.")
    else:
        await message.answer("کار پیدا نشد یا قبلاً تکمیل شده است.")


@router.message(F.text.startswith("/delete_task"))
async def delete_task_handler(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("مثال: /delete_task 3")
        return

    async with SessionFactory() as session:
        deleted = await delete_task(
            session,
            message.from_user.id,
            int(parts[1]),
        )

    if deleted:
        await message.answer("تسک حذف شد.")
    else:
        await message.answer("تسک پیدا نشد.")


@router.message(F.text == "/completed_tasks")
async def completed_tasks_handler(message: Message):
    async with SessionFactory() as session:
        tasks = await list_completed_tasks(
            session,
            message.from_user.id,
        )

    if not tasks:
        await message.answer("هنوز تسک تکمیل‌شده‌ای نداری.")
        return

    text = "\n".join(f"{task.id}. {task.title}" for task in tasks)
    await message.answer(f"تسک‌های تکمیل‌شده:\n\n{text}")


@router.message(F.text == "/today")
async def today_handler(message: Message):
    telegram_id = message.from_user.id

    async with SessionFactory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("ابتدا دستور /start رو اجرا کن.")
            return

        timezone = ZoneInfo(user.timezone)
        now = datetime.now(timezone)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        task_result = await session.execute(
            select(Task).where(
                Task.telegram_id == telegram_id,
                Task.is_completed.is_(False),
            )
        )
        tasks = task_result.scalars().all()

        reminder_result = await session.execute(
            select(Reminder)
            .where(
                Reminder.telegram_id == telegram_id,
                Reminder.is_sent.is_(False),
                Reminder.scheduled_at >= start,
                Reminder.scheduled_at < end,
            )
            .order_by(Reminder.scheduled_at)
        )
        reminders = reminder_result.scalars().all()

    entries = []

    for task in tasks:
        if task.due_at is None:
            continue

        due_at = task.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone)

        if start <= due_at.astimezone(timezone) < end:
            entries.append((
                due_at.astimezone(timezone),
                f"تسک: {task.title} (ID: {task.id})",
            ))

    for reminder in reminders:
        scheduled_at = reminder.scheduled_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone)

        entries.append((
            scheduled_at.astimezone(timezone),
            f"یادآور: {reminder.text}",
        ))

    entries.sort(key=lambda entry: entry[0])

    if not entries:
        await message.answer(
            "برای امروز تسک زمان‌دار یا یادآور ثبت‌شده‌ای نداری."
        )
        return

    lines = [f"برنامه امروز ({now.strftime('%Y-%m-%d')}):", ""]

    for scheduled_at, description in entries:
        lines.append(f"{scheduled_at.strftime('%H:%M')} — {description}")

    untimed_tasks = [task for task in tasks if task.due_at is None]

    if untimed_tasks:
        lines.extend(["", "تسک‌های بدون موعد:"])
        lines.extend(
            f"{task.id}. {task.title}" for task in untimed_tasks
        )

    await message.answer("\n".join(lines))




@router.message(F.text == "/overdue_tasks")
async def overdue_tasks_handler(message: Message):
    try:
        async with SessionFactory() as session:
            result = await session.execute(
                select(User).where(
                    User.telegram_id == message.from_user.id
                )
            )
            user = result.scalar_one_or_none()

            if user is None:
                await message.answer("اطلاعات کاربر پیدا نشد.")
                return

            timezone = ZoneInfo(user.timezone)
            now = datetime.now(timezone)

            tasks = await list_overdue_tasks(
                session,
                message.from_user.id,
                now,
            )

            if not tasks:
                await message.answer("تسک عقب‌افتاده‌ای نداری.")
                return

            lines = ["تسک‌های عقب‌افتاده:\n"]

            for task in tasks:
                due_at = task.due_at.astimezone(timezone)
                lines.append(
                    f"#{task.id} — {task.title}\n"
                    f"موعد: {due_at.strftime('%Y-%m-%d %H:%M')}"
                )

            await message.answer("\n\n".join(lines))

    except Exception:
        logger.exception("Failed to list overdue tasks")
        await message.answer("نمایش تسک‌های عقب‌افتاده با خطا مواجه شد.")


@router.message(F.text.startswith("/edit_task"))
async def edit_task_handler(message: Message):
    try:
        parts = message.text.split(maxsplit=4)

        if len(parts) < 5:
            await message.answer(
                "فرمت صحیح:\n"
                "/edit_task ID YYYY-MM-DD HH:MM عنوان جدید\n\n"
                "مثال:\n"
                "/edit_task 12 2026-10-20 18:00 مطالعه پایتون"
            )
            return

        task_id = int(parts[1])
        due_at = datetime.strptime(
            f"{parts[2]} {parts[3]}",
            "%Y-%m-%d %H:%M",
        )
        title = parts[4].strip()

        if not title:
            await message.answer("عنوان تسک نمی‌تواند خالی باشد.")
            return

        async with SessionFactory() as session:
            # دریافت timezone کاربر
            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == message.from_user.id
                )
            )
            user = user_result.scalar_one_or_none()

            if user is None:
                await message.answer(
                    "اطلاعات کاربر پیدا نشد. ابتدا /start را اجرا کن."
                )
                return

            user_timezone = ZoneInfo(user.timezone)

            # تبدیل تاریخ محلی به datetime دارای timezone
            due_at = due_at.replace(tzinfo=user_timezone)

            if due_at <= datetime.now(user_timezone):
                await message.answer(
                    "موعد تسک باید در آینده باشد."
                )
                return

            result = await update_task(
                session=session,
                telegram_id=message.from_user.id,
                task_id=task_id,
                title=title,
                due_at=due_at,
            )

            if result is None:
                await message.answer("تسکی با این شناسه پیدا نشد.")
                return

        await message.answer(
            f"تسک ویرایش شد.\n"
            f"شناسه: {result.id}\n"
            f"عنوان: {result.title}\n"
            f"موعد: {result.due_at.strftime('%Y-%m-%d %H:%M')}"
        )

    except ValueError:
        await message.answer(
            "شناسه یا تاریخ نامعتبر است. فرمت تاریخ را بررسی کن."
        )

    except Exception:
        logger.exception("Failed to edit task")
        await message.answer(
            "ویرایش تسک با خطا مواجه شد."
        )
