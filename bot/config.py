import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    owner_id: int = int(os.getenv("OWNER_ID", "0"))
    database_url: str = os.getenv("DATABASE_URL", "")
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")
settings = Settings()
if not settings.bot_token or settings.owner_id <= 0 or not settings.database_url:
    raise RuntimeError("Set BOT_TOKEN, OWNER_ID and DATABASE_URL in .env")
