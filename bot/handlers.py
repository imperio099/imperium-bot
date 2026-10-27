import json
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router,F
from aiogram.filters import CommandStart,Command
from aiogram.types import Message,CallbackQuery,LabeledPrice,PreCheckoutQuery
from .config import settings
from .db import db,ensure_user
from .keyboards import menu,shop
router=Router()
PACKS={"p50":(50,100000,"Стартовый"),"p100":(100,204000,"Улучшенный"),"p250":(250,525000,"Выгодный"),"p500":(500,1150000,"Премиум"),"p1000":(1000,2300000,"Элитный"),"p2500":(2500,6250000,"Императорский"),"pvip":(100,0,"VIP")}
async def bal(uid):
 async with db().acquire() as c:return int(await c.fetchval("SELECT balance FROM users WHERE telegram_id=$1",uid) or 0)
async def admin(uid):
 async with db().acquire() as c:return bool(await c.fetchval("SELECT EXISTS(SELECT 1 FROM admins WHERE telegram_id=$1)",uid))
@router.message(CommandStart())
async def start(m:Message):
 await ensure_user(m.from_user); b=await bal(m.from_user.id)
 await m.answer(f"👑 <b>IMPERIUM</b>\n⚜️ Добро пожаловать, {m.from_user.first_name}!\n🪙 Баланс: <b>{b:,}</b> монет",reply_markup=menu())
@router.message(Command("balance"))
async def balance(m:Message):
 await ensure_user(m.from_user); await m.answer(f"🪙 Баланс: <b>{await bal(m.from_user.id):,}</b> монет")
async def claim(uid):
 today=datetime.now(ZoneInfo(settings.timezone)).date()
 async with db().acquire() as c:
  async with c.transaction():
   r=await c.fetchrow("SELECT balance,bonus_date FROM users WHERE telegram_id=$1 FOR UPDATE",uid)
   if r["bonus_date"]==today:return False,int(r["balance"])
   await c.execute("UPDATE users SET balance=balance+2000,bonus_date=$2 WHERE telegram_id=$1",uid,today)
   await c.execute("INSERT INTO transactions(telegram_id,amount,kind,reference) VALUES($1,2000,'daily_bonus',$2)",uid,f"bonus:{uid}:{today}")
   return True,int(r["balance"])+2000
@router.message(Command("bonus"))
async def bonus(m:Message):
 await ensure_user(m.from_user); ok,b=await claim(m.from_user.id)
 await m.answer(f"{'🎁 Получено +2 000 монет!' if ok else '🎁 Бонус уже получен сегодня.'}\n🪙 Баланс: <b>{b:,}</b>")
@router.message(F.reply_to_message,F.text.regexp(r"^н\s+\d+$"))
async def transfer(m:Message):
 s=m.from_user;r=m.reply_to_message.from_user
 if not s or not r or r.is_bot or r.id==s.id: return await m.reply("❌ Нельзя перевести этому пользователю.")
 amount=int(m.text.split()[1])
 if amount<1 or amount>10**12:return await m.reply("❌ Некорректная сумма.")
 await ensure_user(s);await ensure_user(r)
 async with db().acquire() as c:
  async with c.transaction():
   ids=sorted([s.id,r.id]); rows=await c.fetch("SELECT telegram_id,balance FROM users WHERE telegram_id=ANY($1::bigint[]) ORDER BY telegram_id FOR UPDATE",ids)
   balances={int(x["telegram_id"]):int(x["balance"]) for x in rows}
   if balances[s.id]<amount:return await m.reply("❌ Недостаточно монет.")
   await c.execute("UPDATE users SET balance=balance-$2 WHERE telegram_id=$1",s.id,amount)
   await c.execute("UPDATE users SET balance=balance+$2 WHERE telegram_id=$1",r.id,amount)
   ref=f"transfer:{m.chat.id}:{m.message_id}"
   await c.execute("INSERT INTO transactions(telegram_id,amount,kind,reference,details) VALUES($1,$2,'transfer_out',$3,$4::jsonb)",s.id,-amount,ref+":out",json.dumps({"to":r.id}))
   await c.execute("INSERT INTO transactions(telegram_id,amount,kind,reference,details) VALUES($1,$2,'transfer_in',$3,$4::jsonb)",r.id,amount,ref+":in",json.dumps({"from":s.id}))
 await m.reply(f"✅ Переведено <b>{amount:,}</b> монет.")
@router.callback_query(F.data=="home")
async def home(q:CallbackQuery):
 await q.message.edit_text("👑 <b>IMPERIUM</b> — главное меню",reply_markup=menu());await q.answer()
@router.callback_query(F.data=="balance")
async def cb_bal(q:CallbackQuery):
 await ensure_user(q.from_user);await q.message.edit_text(f"🪙 Баланс: <b>{await bal(q.from_user.id):,}</b> монет",reply_markup=menu());await q.answer()
@router.callback_query(F.data=="bonus")
async def cb_bonus(q:CallbackQuery):
 await ensure_user(q.from_user);ok,b=await claim(q.from_user.id)
 await q.message.edit_text(f"{'🎁 Получено +2 000 монет!' if ok else '🎁 Бонус уже получен сегодня.'}\n🪙 Баланс: <b>{b:,}</b>",reply_markup=menu());await q.answer()
@router.callback_query(F.data=="games")
async def games(q:CallbackQuery):
 await q.message.edit_text("🎰 <b>Игры IMPERIUM</b>\nРулетка, кости и колесо фортуны запланированы. Игровой движок не включён в этот стартовый архив до проверки правил ставок и выплат.",reply_markup=menu());await q.answer()
@router.callback_query(F.data=="profile")
async def profile(q:CallbackQuery):
 await ensure_user(q.from_user);await q.message.edit_text(f"👤 <b>Профиль</b>\nID: <code>{q.from_user.id}</code>\n🪙 Баланс: <b>{await bal(q.from_user.id):,}</b>",reply_markup=menu());await q.answer()
@router.callback_query(F.data=="shop")
async def shop_cb(q:CallbackQuery):
 await q.message.edit_text("🛒 <b>Магазин монет</b>\nОплата Telegram Stars ⭐",reply_markup=shop());await q.answer()
@router.callback_query(F.data.startswith("p"))
async def buy(q:CallbackQuery):
 p=PACKS.get(q.data)
 if not p:return await q.answer("Неизвестный пакет",show_alert=True)
 stars,coins,label=p;await ensure_user(q.from_user)
 await q.message.answer_invoice(title=label,description=f"{coins:,} монет" if coins else "VIP-статус",payload=f"imperium:{q.from_user.id}:{q.data}",currency="XTR",prices=[LabeledPrice(label=label,amount=stars)])
 await q.answer()
@router.pre_checkout_query()
async def checkout(q:PreCheckoutQuery):
 parts=q.invoice_payload.split(":")
 if len(parts)!=3 or parts[0]!="imperium" or not parts[1].isdigit() or parts[2] not in PACKS or int(parts[1])!=q.from_user.id or q.currency!="XTR" or q.total_amount!=PACKS[parts[2]][0]:
  return await q.answer(ok=False,error_message="Не удалось проверить заказ.")
 await q.answer(ok=True)
@router.message(F.successful_payment)
async def paid(m:Message):
 pmt=m.successful_payment;parts=pmt.invoice_payload.split(":")
 if len(parts)!=3 or parts[0]!="imperium" or not parts[1].isdigit() or int(parts[1])!=m.from_user.id or parts[2] not in PACKS:
  return await m.answer("Платёж получен, заказ требует проверки. Напишите /paysupport.")
 stars,coins,label=PACKS[parts[2]]
 async with db().acquire() as c:
  async with c.transaction():
   inserted=await c.fetchval("INSERT INTO payments(telegram_payment_charge_id,telegram_id,stars,coins,package) VALUES($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING RETURNING telegram_payment_charge_id",pmt.telegram_payment_charge_id,m.from_user.id,stars,coins,label)
   if inserted and coins:
    await c.execute("UPDATE users SET balance=balance+$2 WHERE telegram_id=$1",m.from_user.id,coins)
    await c.execute("INSERT INTO transactions(telegram_id,amount,kind,reference,details) VALUES($1,$2,'stars_purchase',$3,$4::jsonb)",m.from_user.id,coins,"payment:"+pmt.telegram_payment_charge_id,json.dumps({"stars":stars,"package":label}))
   elif inserted:
    await c.execute("INSERT INTO transactions(telegram_id,amount,kind,reference,details) VALUES($1,0,'vip_purchase',$2,$3::jsonb)",m.from_user.id,"payment:"+pmt.telegram_payment_charge_id,json.dumps({"stars":stars}))
 await m.answer("✅ Оплата подтверждена. "+(f"Начислено {coins:,} монет." if coins else "Покупка VIP зарегистрирована; преимущества VIP нужно настроить отдельно."))
@router.callback_query(F.data=="top")
async def top(q:CallbackQuery):
 async with db().acquire() as c:rows=await c.fetch("SELECT first_name,balance FROM users WHERE is_blocked=FALSE ORDER BY balance DESC LIMIT 10")
 lines=["🏆 <b>Рейтинг IMPERIUM</b>"]+[f"{i}. {r['first_name'][:24]} — {int(r['balance']):,}" for i,r in enumerate(rows,1)]
 await q.message.edit_text("\n".join(lines),reply_markup=menu());await q.answer()
@router.callback_query(F.data=="help")
async def help_cb(q:CallbackQuery):
 await q.message.edit_text("❓ /start — меню\n/balance — баланс\n/bonus — бонус\nОтветьте на сообщение: н 100000\n/paysupport — вопросы платежей",reply_markup=menu());await q.answer()
@router.message(Command("paysupport"))
async def paysupport(m:Message):await m.answer("По вопросам платежей сохраните чек, укажите Telegram ID и дату покупки и обратитесь к владельцу бота.")
@router.message(Command("admin"))
async def admin_panel(m:Message):
 if not await admin(m.from_user.id):return await m.answer("⛔ Доступ запрещён.")
 await m.answer("👑 <b>Админ-панель</b>\n/admin_add ID AMOUNT — начислить\n/admin_take ID AMOUNT — списать\n/admin_balance ID AMOUNT — установить баланс")
async def change(m:Message,mode):
 if not await admin(m.from_user.id):return await m.answer("⛔ Доступ запрещён.")
 x=(m.text or "").split()
 if len(x)!=3 or not x[1].isdigit() or not x[2].isdigit():return await m.answer("Формат: /admin_add ID AMOUNT")
 uid,amt=int(x[1]),int(x[2])
 if amt>10**12:return await m.answer("Сумма слишком большая.")
 async with db().acquire() as c:
  async with c.transaction():
   r=await c.fetchrow("SELECT balance FROM users WHERE telegram_id=$1 FOR UPDATE",uid)
   if not r:return await m.answer("Игрок не найден — пусть сначала запустит бота.")
   old=int(r["balance"])
   if mode=="take" and old<amt:return await m.answer("Недостаточно монет.")
   new=old+amt if mode=="add" else old-amt if mode=="take" else amt
   await c.execute("UPDATE users SET balance=$2 WHERE telegram_id=$1",uid,new)
   await c.execute("INSERT INTO transactions(telegram_id,amount,kind,details) VALUES($1,$2,$3,$4::jsonb)",uid,new-old,"admin_"+mode,json.dumps({"admin":m.from_user.id,"old":old,"new":new}))
 await m.answer(f"✅ Баланс: {old:,} → {new:,}")
@router.message(Command("admin_add"))
async def add(m:Message):await change(m,"add")
@router.message(Command("admin_take"))
async def take(m:Message):await change(m,"take")
@router.message(Command("admin_balance"))
async def setbal(m:Message):await change(m,"set")
