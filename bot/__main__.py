import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from .config import settings
from .db import init_db
from .handlers import router


async def health(request):
return web.Response(text="IMPERIUM is running")


async def main():
await init_db(settings.owner_id)


bot = Bot(
    settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
dp.include_router(router)

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/health", health)

runner = web.AppRunner(app)
await runner.setup()

port = int(os.getenv("PORT", "4027"))
site = web.TCPSite(runner, "0.0.0.0", port)
await site.start()

try:
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )
finally:
    await runner.cleanup()
    await bot.session.close()



if name == "main":
asyncio.run(main())


