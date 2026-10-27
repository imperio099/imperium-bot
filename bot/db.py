import asyncpg
from .config import settings
pool = None
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(
 telegram_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT NOT NULL DEFAULT '',
 balance BIGINT NOT NULL DEFAULT 0 CHECK(balance >= 0), bonus_date DATE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), is_blocked BOOLEAN NOT NULL DEFAULT FALSE);
CREATE TABLE IF NOT EXISTS transactions(
 id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
 amount BIGINT NOT NULL, kind TEXT NOT NULL, reference TEXT UNIQUE,
 details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS admins(telegram_id BIGINT PRIMARY KEY, added_by BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS payments(
 telegram_payment_charge_id TEXT PRIMARY KEY, telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
 stars INTEGER NOT NULL, coins BIGINT NOT NULL, package TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
'''
async def init_db(owner_id):
 global pool
 pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10, command_timeout=20)
 async with pool.acquire() as c:
  await c.execute(SCHEMA)
  await c.execute('INSERT INTO admins(telegram_id,added_by) VALUES($1,$1) ON CONFLICT DO NOTHING', owner_id)
def db():
 if pool is None: raise RuntimeError("Database not initialized")
 return pool
async def ensure_user(user):
 async with db().acquire() as c:
  await c.execute('''INSERT INTO users(telegram_id,username,first_name) VALUES($1,$2,$3)
  ON CONFLICT(telegram_id) DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name''', user.id,user.username,user.first_name or '')
