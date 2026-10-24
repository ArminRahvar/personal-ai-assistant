from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋 تسک‌ها"),
            KeyboardButton(text="➕ افزودن تسک"),
        ],
        [
            KeyboardButton(text="📅 برنامه امروز"),
            KeyboardButton(text="⏰ یادآورها"),
        ],
        [
            KeyboardButton(text="🧠 حافظه‌ها"),
            KeyboardButton(text="❔ راهنما"),
        ],
        [
            KeyboardButton(text="➕ یادآور"),
            KeyboardButton(text="⚙️ تنظیمات"),
        ],
        [KeyboardButton(text="💬 گفت‌وگو")],
    ],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="پیام یا دستور بنویسید…",
)
