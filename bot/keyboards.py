from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def menu():
 rows=[
  [InlineKeyboardButton(text="🪙 Мой баланс",callback_data="balance"),InlineKeyboardButton(text="🎁 Бонус",callback_data="bonus")],
  [InlineKeyboardButton(text="🎰 Игры",callback_data="games"),InlineKeyboardButton(text="👤 Профиль",callback_data="profile")],
  [InlineKeyboardButton(text="🛒 Магазин монет",callback_data="shop")],
  [InlineKeyboardButton(text="🏆 Рейтинг",callback_data="top"),InlineKeyboardButton(text="❓ Помощь",callback_data="help")]]
 return InlineKeyboardMarkup(inline_keyboard=rows)
def shop():
 items=[("⭐ 50 — 100 000","p50"),("⭐ 100 — 204 000 (+2%)","p100"),("⭐ 250 — 525 000 (+5%)","p250"),("⭐ 500 — 1 150 000 (+10%)","p500"),("⭐ 1 000 — 2 300 000 (+15%)","p1000"),("⭐ 2 500 — 6 250 000 (+25%)","p2500"),("👑 VIP — 100 Stars","pvip"),("⬅️ Назад","home")]
 return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t,callback_data=c)] for t,c in items])
