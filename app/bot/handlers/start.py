
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.keyboards import MAIN_MENU
from app.database.connection import SessionFactory
from app.services.user_service import get_or_create_user

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    if not message.from_user:
        return

    async with SessionFactory() as session:
        await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            language=message.from_user.language_code or "fa",
        )

    await message.answer(
        f"سلام {message.from_user.first_name or ''}! 👋\n"
        "من دستیار شخصی شما هستم. از دکمه‌های پایین برای دسترسی سریع استفاده کنید "
        "یا همین‌جا پیام بفرستید تا گفت‌وگو کنیم.\n\n"
        "حافظه خودکار در حال حاضر خاموش است؛ هر زمان خواستید با /memory_on "
        "فعال و با /memory_off غیرفعالش کنید.",
        reply_markup=MAIN_MENU,
    )


@router.message(Command("help"))
@router.message(F.text == "❔ راهنما")
async def help_handler(message: Message):
    await message.answer(
        "راهنمای دستیار شخصی\n\n"
        "💬 گفت‌وگو: هر پیام متنی بفرستید.\n\n"
        "📋 تسک‌ها:\n"
        "دکمه «تسک‌ها» برای دیدن کارهای باز\n"
        "/add_task عنوان — افزودن کار\n"
        "/add_task YYYY-MM-DD HH:MM عنوان — افزودن کار زمان‌دار\n"
        "/complete_task ID — تکمیل کار\n"
        "/edit_task ID YYYY-MM-DD HH:MM عنوان — ویرایش کار زمان‌دار\n"
        "/delete_task ID — حذف کار\n"
        "/completed_tasks — کارهای انجام‌شده\n"
        "/overdue_tasks — کارهای عقب‌افتاده\n"
        "دکمه «برنامه امروز» — دیدن برنامه امروز\n\n"
        "⏰ یادآورها:\n"
        "/remind YYYY-MM-DD HH:MM متن — ساخت یادآور\n"
        "دکمه «یادآورها» — دیدن یادآورهای در انتظار\n"
        "دکمه «یادآور» — راهنمای ساخت یادآور\n"
        "/delete_reminder ID — حذف یادآور\n\n"
        "🧠 حافظه:\n"
        "/remember متن — ذخیره حافظه\n"
        "دکمه «حافظه‌ها» — دیدن حافظه‌های ذخیره‌شده\n"
        "/forget ID — حذف حافظه\n"
        "/memory_on و /memory_off — روشن/خاموش‌کردن حافظه خودکار\n\n"
        "تنظیمات:\n"
        "/timezone Asia/Tehran — تنظیم منطقه زمانی\n"
        "/clear_history — پاک‌کردن تاریخچه گفت‌وگو",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text == "➕ افزودن تسک")
async def add_task_help_handler(message: Message):
    await message.answer(
        "برای افزودن کار یکی از این روش‌ها را بنویسید:\n"
        "• /add_task مطالعه پایتون\n"
        "• /add_task YYYY-MM-DD HH:MM مطالعه پایتون\n\n"
        "همچنین می‌توانید طبیعی بنویسید: «فردا ساعت ۶ مطالعه پایتون را انجام می‌دهم».",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text == "💬 گفت‌وگو")
async def chat_help_handler(message: Message):
    await message.answer(
        "هر چیزی دوست دارید بپرسید یا درباره‌اش صحبت کنید. "
        "برای ساخت تسک یا یادآور هم درخواستتان را به زبان طبیعی بنویسید.",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text == "⚙️ تنظیمات")
async def settings_handler(message: Message):
    await message.answer(
        "تنظیمات:\n"
        "• /timezone Asia/Tehran — تغییر منطقه زمانی\n"
        "• /memory_on — فعال‌کردن حافظه خودکار\n"
        "• /memory_off — غیرفعال‌کردن حافظه خودکار\n"
        "• /clear_history — پاک‌کردن تاریخچه گفت‌وگو",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text == "➕ یادآور")
async def add_reminder_help_handler(message: Message):
    await message.answer(
        "برای ساخت یادآور، تاریخ و ساعت را مشخص کنید:\n"
        "/remind YYYY-MM-DD HH:MM خرید نان\n\n"
        "یا طبیعی بنویسید: «فردا ساعت ۹ خرید نان را یادآوری کن».",
        reply_markup=MAIN_MENU,
    )
