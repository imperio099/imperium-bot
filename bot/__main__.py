import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "4027"))
balances = {}

async def health(request):
    return web.Response(text="IMPERIUM trial is running")

async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message):
        uid = message.from_user.id
        balances.setdefault(uid, 0)
        await message.answer(
            "👑 <b>IMPERIUM — пробная версия</b>\n"
            f"Привет, {message.from_user.first_name}!\n"
            f"🪙 Баланс: <b>{balances[uid]:,}</b> монет\n\n"
            "Команды: /balance, /bonus"
        )

    @dp.message(Command("balance"))
    async def balance(message: Message):
        uid = message.from_user.id
        balances.setdefault(uid, 0)
        await message.answer(
            f"🪙 Баланс: <b>{balances[uid]:,}</b> монет"
        )

    @dp.message(Command("bonus"))
    async def bonus(message: Message):
        uid = message.from_user.id
        balances.setdefault(uid, 0)
        balances[uid] += 2000
        await message.answer(
            f"🎁 Бонус +2 000 монет!\n"
            f"🪙 Баланс: <b>{balances[uid]:,}</b>"
        )

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"IMPERIUM trial running on port {PORT}", flush=True)

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
