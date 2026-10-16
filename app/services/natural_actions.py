
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI
from sqlalchemy import select

from app.core.config import get_settings
from app.database.connection import SessionFactory
from app.database.models import User
from app.services.task_service import add_task
from app.services.reminder_service import create_reminder

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.llm_api_key or "ollama",
    base_url=settings.llm_base_url,
)


async def handle_natural_action(text: str, telegram_id: int) -> str | None:
    try:
        async with SessionFactory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user is None:
                return None

            timezone = ZoneInfo(user.timezone)
            now = datetime.now(timezone)

            response = await client.chat.completions.create(
                model=settings.llm_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify the user's message as a task, reminder, "
                            "or normal chat. Return JSON only with fields: "
                            "action ('task', 'reminder', or 'none'), "
                            "title (string), datetime (local ISO format "
                            "YYYY-MM-DDTHH:MM or null). "
                            "Only choose task or reminder when the user "
                            "clearly asks to create one. Resolve relative "
                            "dates using the supplied current local time. "
                            "Do not invent dates or times. For a task without "
                            "a deadline, datetime must be null. "
                            "Current local time: "
                            f"{now.strftime('%Y-%m-%d %H:%M')} "
                            f"Timezone: {user.timezone}"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )

            data = json.loads(response.choices[0].message.content or "{}")
            action = data.get("action")
            title = data.get("title", "").strip()
            date_text = data.get("datetime")

            if action not in ("task", "reminder") or not title:
                return None

            due_at = None
            if date_text:
                due_at = datetime.fromisoformat(date_text).replace(
                    tzinfo=timezone
                )

                if due_at <= now:
                    return "زمانی که مشخص کردی گذشته؛ لطفاً یک زمان آینده انتخاب کن."

            if action == "reminder":
                if due_at is None:
                    return "برای تنظیم یادآور، تاریخ و ساعت رو هم مشخص کن."

                await create_reminder(
                    session,
                    telegram_id,
                    title,
                    due_at,
                )
                return (
                    f"یادآور ثبت شد: {title}\n"
                    f"زمان: {due_at.strftime('%Y-%m-%d %H:%M')}"
                )

            task = await add_task(
                session,
                telegram_id,
                title,
                due_at=due_at,
            )

            if due_at:
                await create_reminder(
                    session,
                    telegram_id,
                    f"موعد انجام تسک: {title}",
                    due_at,
                )

            result_text = f"تسک ثبت شد: {task.title}"

            if due_at:
                result_text += (
                    f"\nموعد: {due_at.strftime('%Y-%m-%d %H:%M')}"
                    "\nیادآور هم تنظیم شد."
                )

            return result_text

    except Exception:
        logger.exception("Natural action handling failed")
        return None
