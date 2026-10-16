
import json

from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
)


async def extract_memory(message: str) -> dict | None:
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": """
Extract a useful, lasting fact or preference about the user.

Return JSON only:
{
  "content": "short statement",
  "category": "interest|preference|goal|personal|work|other",
  "importance": 1
}

Importance must be an integer from 1 to 5.
If there is no useful lasting information, return exactly NONE.
Do not extract questions, temporary states, or facts about other people.
"""
            },
            {"role": "user", "content": message},
        ],
        temperature=0,
    )

    result = response.choices[0].message.content
    if not result or result.strip().upper() == "NONE":
        return None

    try:
        data = json.loads(result)
        content = data.get("content", "").strip()
        category = data.get("category", "other")
        importance = int(data.get("importance", 3))

        if not content or not 1 <= importance <= 5:
            return None

        return {
            "content": content,
            "category": category,
            "importance": importance,
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
