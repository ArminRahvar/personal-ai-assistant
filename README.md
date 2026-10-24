# Personal AI Assistant

A Telegram personal assistant with Persian-language chat, task and reminder
management, conversation history, and optional saved memories.

## Requirements

- Python 3.12 or newer
- PostgreSQL
- A Telegram bot token
- An OpenAI-compatible chat completions endpoint and API key

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a PostgreSQL database, then set these environment variables (or put
them in a local `.env` file):

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes for runtime | `postgresql+asyncpg://localhost/personal_ai_assistant` | Async SQLAlchemy connection URL |
| `TELEGRAM_BOT_TOKEN` | Bot worker only | — | Telegram bot token |
| `LLM_API_KEY` | For LLM calls | — | Key for the chat completions endpoint |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model name accepted by the endpoint |
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

Keep `.env` and all real credentials out of source control. Apply migrations:

```bash
alembic upgrade head
```

## Run

The web API and Telegram bot are separate processes. Run one bot worker and
one or more web workers:

```bash
# Terminal 1: Telegram polling and reminder delivery
python -m app.bot_worker

# Terminal 2: HTTP health/readiness API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`GET /health` is a liveness check. `GET /ready` checks database connectivity
and returns HTTP 503 when the database cannot be reached. Run only one polling
worker per bot token; Telegram polling does not support multiple concurrent
pollers for the same token.

## Bot commands

Send `/help` to the bot for the complete command list. Common commands include
`/tasks`, `/add_task`, `/reminders`, `/remind`, `/timezone`, and `/clear_history`.
Automatic memory extraction and use are **off by default**. Use `/memory_on`
to opt in and `/memory_off` to turn them off again. Existing memories remain
stored when turned off; inspect them with `/memories` and remove them with
`/forget ID`. `/remember TEXT` explicitly saves a memory regardless of the
automatic-memory setting.

Normal messages are sent to the configured LLM endpoint for task/reminder
detection and chat responses. The memory setting controls long-term memory
extraction and whether saved memories are added to chat context; it does not
disable LLM processing or conversation-history storage. Use `/clear_history`
to clear stored conversation messages.

## Tests

```bash
python -m pytest -q
python -m compileall -q app migrations
alembic heads
```
