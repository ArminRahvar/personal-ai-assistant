from app.bot.keyboards import MAIN_MENU


def test_main_menu_has_primary_navigation_buttons():
    labels = {
        button.text
        for row in MAIN_MENU.keyboard
        for button in row
    }

    assert labels == {
        "📋 تسک‌ها",
        "➕ افزودن تسک",
        "📅 برنامه امروز",
        "⏰ یادآورها",
        "🧠 حافظه‌ها",
        "❔ راهنما",
        "➕ یادآور",
        "⚙️ تنظیمات",
        "💬 گفت‌وگو",
    }
    assert MAIN_MENU.resize_keyboard is True
    assert MAIN_MENU.is_persistent is True
