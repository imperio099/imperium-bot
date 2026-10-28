import os
import json
import time
import random
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "4027"))

balances = {}
busy = set()

def api(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    body = urllib.parse.urlencode(data or {}).encode()
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read())

def send(chat, text):
    api("sendMessage", {"chat_id": chat, "text": text})

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"IMPERIUM ROULETTE OK")

    def log_message(self, *args):
        pass

def handle(update):
    msg = update.get("message")
    if not msg or not msg.get("text"):
        return

    chat = msg["chat"]["id"]
    uid = msg["from"]["id"]
    text = msg["text"].strip().lower()

    balances.setdefault(uid, 1000)

    if text.startswith("/start"):
        send(chat,
            "👑 IMPERIUM CASINO\n\n"
            "🎰 Европейская рулетка: 0–36\n"
            "🪙 Стартовый баланс: 1 000 монет\n\n"
            "/balance — баланс\n"
            "/roulette 100 — ставка 100 монет\n\n"
            "Выпало 0 — ставка проиграна.\n"
            "Число 1–36 — выигрыш зависит от ставки."
        )

    elif text.startswith("/balance"):
        send(chat, f"🪙 Твой баланс: {balances[uid]} монет")

    elif text.startswith("/roulette"):
        if chat in busy:
            send(chat, "⏳ Рулетка уже крутится!")
            return

        parts = text.split()

        if len(parts) != 2 or not parts[1].isdigit():
            send(chat, "Используй: /roulette 100")
            return

        bet = int(parts[1])

        if bet < 1 or bet > balances[uid]:
            send(chat, f"❌ Ставка должна быть от 1 до {balances[uid]} монет.")
            return

        busy.add(chat)

        try:
            number = random.randint(0, 36)
            balances[uid] -= bet

            if number == 0:
                send(chat,
                    f"🎰 Выпало: 0\n"
                    f"❌ Ты проиграл {bet} монет.\n"
                    f"🪙 Баланс: {balances[uid]}"
                )
            else:
                prize = bet * 36
                balances[uid] += prize
                send(chat,
                    f"🎰 Выпало: {number}\n"
                    f"🎉 Джекпот! Выигрыш: {prize} монет.\n"
                    f"🪙 Баланс: {balances[uid]}"
                )
        finally:
            busy.discard(chat)

def main():
    if not TOKEN:
        print("ОШИБКА: BOT_TOKEN не найден", flush=True)
        return

    server = HTTPServer(("0.0.0.0", PORT), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"IMPERIUM ROULETTE запущен на порту {PORT}", flush=True)

    offset = 0

    while True:
        try:
            result = api("getUpdates", {
                "offset": offset,
                "timeout": 20
            })

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle(update)
                except Exception as e:
                    print(f"Ошибка: {e}", flush=True)

        except Exception as e:
            print(f"Ошибка Telegram: {e}", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    main()
