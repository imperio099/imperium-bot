import asyncio
from aiogram import Bot,Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from .config import settings
from .db import init_db
from .handlers import router
async def main():
 await init_db(settings.owner_id)
 bot=Bot(settings.bot_token,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
 dp=Dispatcher(); dp.include_router(router)
 await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())
if __name__=="__main__": asyncio.run(main())
