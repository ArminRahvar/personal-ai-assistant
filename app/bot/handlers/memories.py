
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.connection import SessionFactory
from app.services.memory_service import (
    save_memory,
    list_memories,
    delete_memory,
)
from app.services.user_service import set_user_memory_enabled

router = Router()


@router.message(Command("memory_on"))
async def memory_on_handler(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        updated = await set_user_memory_enabled(
            session,
            message.from_user.id,
            enabled=True,
        )

    await message.answer(
        "حافظه خودکار فعال شد. پیام‌های بعدی ممکن است برای ذخیره اطلاعات پایدار بررسی شوند."
        if updated
        else "ابتدا دستور /start را اجرا کنید."
    )


@router.message(Command("memory_off"))
async def memory_off_handler(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        updated = await set_user_memory_enabled(
            session,
            message.from_user.id,
            enabled=False,
        )

    await message.answer(
        "حافظه خودکار غیرفعال شد؛ حافظه‌های قبلی باقی می‌مانند و در پاسخ‌ها استفاده نمی‌شوند. "
        "برای حذف آن‌ها از /memories و /forget استفاده کنید."
        if updated
        else "ابتدا دستور /start را اجرا کنید."
    )



@router.message(Command("remember"))
async def remember_handler(message: Message):
    if not message.from_user:
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "برای ذخیره اطلاعات بنویس:\n"
            "/remember من قهوه تلخ دوست دارم"
        )
        return

    async with SessionFactory() as session:
        memory = await save_memory(
            session,
            message.from_user.id,
            parts[1],
        )

    await message.answer(f"ذخیره شد. شناسه حافظه:\n{memory.id}")


@router.message(Command("memories"))
async def memories_handler(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        memories = await list_memories(session, message.from_user.id)

    if not memories:
        await message.answer("حافظه‌ای ذخیره نشده است.")
        return

    lines = ["حافظه‌های ذخیره‌شده:"]
    for memory in memories:
        lines.append(
            f"\nشناسه: {memory.id}\n"
            f"اهمیت: {memory.importance}/5\n"
            f"متن: {memory.content}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("forget"))
async def forget_handler(message: Message):
    if not message.from_user:
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer(
            "برای حذف حافظه بنویس:\n/forget شناسه"
        )
        return

    async with SessionFactory() as session:
        deleted = await delete_memory(
            session,
            message.from_user.id,
            parts[1].strip(),
        )

    await message.answer(
        "حافظه حذف شد." if deleted else "حافظه‌ای با این شناسه پیدا نشد."
    )
