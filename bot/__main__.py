import os
import json
import time
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from html import escape

TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "4027"))

balances = {}
bonus_used = set()
offset = 0

def api(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    body = urllib.parse.urlencode(data or {}).encode()
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read().decode())

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"IMPERIUM trial is running")

    def log_message(self, *args):
        pass

def send(chat_id, text):
    api("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })

def handle(update):
    message = update.get("message")
    if not message or not message.get("text"):
        return

    user = message.get("from", {})
    uid = user.get("id")
    chat = message["chat"]["id"]
    name = escape(user.get("first_name", "Император"))
    text = message["text"].split()[0].split("@")[0].lower()

    if not uid:
        return

    balances.setdefault(uid, 0)

    if text == "/start":
        send(chat,
            f"👑 <b>IMPERIUM — пробная версия</b>\n"
            f"Привет, {name}!\n"
            f"🪙 Баланс: <b>{balances[uid]:,}</b> монет\n\n"
            "/balance — проверить баланс\n"
            "/bonus — получить 2 000 монет"
        )

    elif text == "/balance":
        send(chat, f"🪙 Баланс: <b>{balances[uid]:,}</b> монет")

    elif text == "/bonus":
        if uid in bonus_used:
            send(chat, "🎁 Ты уже получал бонус в этой сессии.")
        else:
            balances[uid] += 2000
            bonus_used.add(uid)
            send(chat,
                f"🎁 Получено <b>+2 000</b> монет!\n"
                f"🪙 Баланс: <b>{balances[uid]:,}</b>"
            )

def main():
    global offset

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    server = HTTPServer(("0.0.0.0", PORT), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"IMPERIUM запущен на порту {PORT}", flush=True)

    while True:
        try:
            result = api("getUpdates", {
                "offset": offset,
                "timeout": 25
            })

            if not result.get("ok"):
                print("Ошибка Telegram API", flush=True)
                time.sleep(3)
                continue

            for update in result["result"]:
                offset = update["update_id"] + 1
                try:
                    handle(update)
                except Exception as e:
                    print(f"Ошибка обработки: {e}", flush=True)

        except Exception as e:
            print(f"Ошибка соединения: {e}", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    main()
