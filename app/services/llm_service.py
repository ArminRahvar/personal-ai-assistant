import asyncio
import logging
from sqlalchemy import select

from app.core.config import get_settings
from app.database.connection import SessionFactory
from app.database.models import ConversationMessage, User
from app.services.memory_service import list_memories
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError
settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.llm_api_key or "ollama",
    base_url=settings.llm_base_url,
)


logger = logging.getLogger(__name__)


async def request_with_retry(messages: list[dict]) -> str:
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content or "نتونستم پاسخی تولید کنم."

        except (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError):
            if attempt == 2:
                logger.exception("LLM request failed after 3 attempts")
                raise

            await asyncio.sleep(2 ** attempt)

async def generate_response(message: str, telegram_id: int) -> str:
    async with SessionFactory() as session:
        user_result = await session.execute(
            select(User.memory_enabled).where(User.telegram_id == telegram_id)
        )
        memory_enabled = user_result.scalar_one_or_none() is True
        memories = (
            await list_memories(session, telegram_id)
            if memory_enabled
            else []
        )

        result = await session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.telegram_id == telegram_id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(12)
        )
        history = list(reversed(result.scalars().all()))

        memory_context = "\n".join(
            f"- {memory.content}" for memory in memories
        )

        system_prompt = (
            "You are a general-purpose personal AI assistant. "
            "Answer the latest user message directly and naturally. "
            "Use saved memories only when relevant. "
            "Reply in the user's language. Be clear and practical."
        )

        if memory_context:
            system_prompt += (
                "\n\nRelevant information remembered about this user:\n"
                + memory_context
            )

        messages = [{"role": "system", "content": system_prompt}]

        for item in history:
            if item.role in ("user", "assistant"):
                messages.append({
                    "role": item.role,
                    "content": item.content,
                })

        messages.append({"role": "user", "content": message})

        answer = await request_with_retry(messages)

        session.add_all([
            ConversationMessage(
                telegram_id=telegram_id,
                role="user",
                content=message,
            ),
            ConversationMessage(
                telegram_id=telegram_id,
                role="assistant",
                content=answer,
            ),
        ])
        await session.commit()

        return answer
