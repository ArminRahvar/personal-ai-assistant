
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bot.bot import bot, dp



from app.services.reminder_scheduler import reminder_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = asyncio.create_task(dp.start_polling(bot))
    scheduler_task = asyncio.create_task(reminder_scheduler())

    try:
        yield
    finally:
        scheduler_task.cancel()
        polling_task.cancel()

        await asyncio.gather(
            scheduler_task,
            polling_task,
            return_exceptions=True,
        )
        await bot.session.close()


app = FastAPI(title="Personal AI Assistant", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
