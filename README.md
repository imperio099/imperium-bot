# IMPERIUM starter

This is a first runnable foundation, not the complete production bot. It includes a Telegram bot, PostgreSQL persistence, balances, daily bonus, reply-based transfers, basic admin balance tools, a Stars shop with payment-idempotency, profiles and leaderboards. Game buttons are placeholders until the round engine is implemented and load-tested.

## Start
1. Install Docker Desktop / Docker Engine with Compose.
2. Copy `.env.example` to `.env`.
3. Create the bot using Telegram's official `@BotFather`, and put its token in `BOT_TOKEN`.
4. Set `OWNER_ID` to your numeric Telegram user ID.
5. Replace the sample password in both `DB_PASSWORD` and `DATABASE_URL` with the same long random password.
6. Run `docker compose up --build -d`
7. View logs with `docker compose logs -f bot`

## Commands
- `/start` — menu
- `/balance` — balance
- `/bonus` — 2,000 coins once per Moscow calendar day
- Reply to a user's message with `н 100000` — transfer coins
- `/games` is represented by the Games button
- `/admin` — admin panel summary
- `/admin_add ID AMOUNT`, `/admin_take ID AMOUNT`, `/admin_balance ID AMOUNT` — owner/admin balance tools

## Production checklist
Do not share the `.env` file or bot token. Configure encrypted off-host backups and monitoring. Test concurrent transactions and recovery. Add an actual support workflow. Verify Telegram Stars policies and applicable laws before using paid chance-based games. Do not promise zero downtime; no server is infallible.
