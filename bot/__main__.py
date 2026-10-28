import os
import json
import time
import random
import threading
import urllib.request
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "4027"))
DATA = Path("/app/casino_data.json")

balances, histories, bonuses, busy = {}, {}, {}, set()

RED = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36
}


def load():
    global balances, histories, bonuses
    try:
        d = json.loads(DATA.read_text())
        balances = {int(k): int(v) for k, v in d.get("balances", {}).items()}
        histories = {int(k): v for k, v in d.get("histories", {}).items()}
        bonuses = {int(k): v for k, v in d.get("bonuses", {}).items()}
    except FileNotFoundError:
        pass
    except Exception as e:
        print("Load error:", e, flush=True)


def save():
    try:
        tmp = DATA.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "balances": balances,
            "histories": histories,
            "bonuses": bonuses
        }))
        tmp.replace(DATA)
    except Exception as e:
        print("Save error:", e, flush=True)


def api(method, data=None):
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + TOKEN + "/" + method,
        data=urllib.parse.urlencode(data or {}).encode()
    )
    with urllib.request.urlopen(req, timeout=35) as r:
        result = json.loads(r.read())

    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram API error"))

    return result.get("result")


def send(chat, text, kb=None):
    d = {"chat_id": chat, "text": text}
    if kb:
        d["reply_markup"] = json.dumps(kb, ensure_ascii=False)
    return api("sendMessage", d)


def edit(chat, mid, text, kb=None):
    if mid is None:
        return

    d = {"chat_id": chat, "message_id": mid, "text": text}
    if kb:
        d["reply_markup"] = json.dumps(kb, ensure_ascii=False)

    try:
        api("editMessageText", d)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print("Edit error:", e, flush=True)


def answer(qid):
    try:
        api("answerCallbackQuery", {"callback_query_id": qid})
    except Exception:
        pass


def menu():
    return {
        "inline_keyboard": [
            [
                {"text": "🎰 Играть", "callback_data": "play"},
                {"text": "🪙 Баланс", "callback_data": "bal"}
            ],
            [
                {"text": "📜 История", "callback_data": "hist"},
                {"text": "🎁 Бонус +250", "callback_data": "bonus"}
            ]
        ]
    }


def bets():
    return {
        "inline_keyboard": [
            [
                {"text": "10 🪙", "callback_data": "bet:10"},
                {"text": "50 🪙", "callback_data": "bet:50"}
            ],
            [
                {"text": "100 🪙", "callback_data": "bet:100"},
                {"text": "500 🪙", "callback_data": "bet:500"}
            ],
            [
                {"text": "✍️ Другая сумма", "callback_data": "custom"},
                {"text": "⬅️ Меню", "callback_data": "menu"}
            ]
        ]
    }


def types(b):
    return {
        "inline_keyboard": [
            [
                {"text": "🔴 Красное (2×)", "callback_data": f"spin:{b}:red"},
                {"text": "⚫ Чёрное (2×)", "callback_data": f"spin:{b}:black"}
            ],
            [
                {"text": "🟢 Зеро (36×)", "callback_data": f"spin:{b}:zero"},
                {"text": "🎯 Число (36×)", "callback_data": f"num:{b}"}
            ],
            [{"text": "⬅️ Назад", "callback_data": "play"}]
        ]
    }


def number_buttons(b):
    rows = []

    for n in range(0, 37, 6):
        rows.append([
            {"text": str(x), "callback_data": f"pick:{b}:{x}"}
            for x in range(n, min(n + 6, 37))
        ])

    rows.append([{"text": "⬅️ Назад", "callback_data": f"bet:{b}"}])

    return {"inline_keyboard": rows}


def color(n):
    if n == 0:
        return "🟢 ЗЕЛЁНОЕ"
    return "🔴 КРАСНОЕ" if n in RED else "⚫ ЧЁРНОЕ"


def history(uid, line):
    histories.setdefault(uid, []).insert(0, line)
    histories[uid] = histories[uid][:10]


def spin(chat, uid, b, kind, target, mid):
    if chat in busy:
        send(chat, "⏳ Рулетка уже крутится. Подожди немного.")
        return

    balances.setdefault(uid, 1000)

    if b < 1 or b > balances[uid]:
        edit(
            chat, mid,
            f"❌ Недостаточно монет. Баланс: {balances[uid]}",
            menu()
        )
        return

    busy.add(chat)

    try:
        balances[uid] -= b

        result = send(
            chat,
            f"👑 IMPERIUM CASINO\n\n"
            f"🎰 Ставка: {b} монет\n"
            f"🎡 Рулетка запускается…"
        )

        spin_mid = result["message_id"]

        frames = [
            "🔴 17   ⚫ 8   🔴 23   ⚫ 14",
            "⚫ 26   🔴 3   ⚫ 35   🔴 12",
            "🔴 19   ⚫ 10   🔴 5   ⚫ 24",
            "⚫ 30   🔴 7   ⚫ 28   🔴 1"
        ]

        number = random.randint(0, 36)

        for frame in frames:
            time.sleep(0.55)
            edit(
                chat,
                spin_mid,
                f"👑 IMPERIUM CASINO\n\n"
                f"🎰 Ставка: {b} монет\n"
                f"🎡 Рулетка крутится…\n\n{frame}"
            )

        won = (
            (kind == "red" and number in RED)
            or (
                kind == "black"
                and number != 0
                and number not in RED
            )
            or (kind == "zero" and number == 0)
            or (kind == "number" and number == target)
        )

        payout = b * (
            36 if kind in ("zero", "number") else 2
        ) if won else 0

        balances[uid] += payout
        net = payout - b

        history(
            uid,
            f"{number} ({color(number)}) — {net:+} монет"
        )

        save()

        outcome = (
            f"🎉 Выигрыш: +{payout} монет"
            if won
            else f"❌ Проигрыш: −{b} монет"
        )

        edit(
            chat,
            spin_mid,
            f"👑 IMPERIUM CASINO\n\n"
            f"🎰 Выпало: {number}\n"
            f"{color(number)}\n\n"
            f"{outcome}\n"
            f"🪙 Баланс: {balances[uid]} монет",
            menu()
        )

    except Exception as e:
        print("Spin error:", e, flush=True)
        send(
            chat,
            "⚠️ Ошибка во время игры. Попробуй ещё раз через минуту.",
            menu()
        )

    finally:
        busy.discard(chat)


def message(m):
    if not m or not m.get("text"):
        return

    chat = m["chat"]["id"]
    uid = m["from"]["id"]
    txt = m["text"].strip()

    balances.setdefault(uid, 1000)

    if txt.startswith("/start"):
        save()
        send(
            chat,
            "👑 IMPERIUM CASINO\n\n"
            "🎰 Европейская рулетка: 0–36\n"
            "🪙 Стартовый баланс: 1 000 монет\n\n"
            "Выбирай кнопки ниже.\n"
            "🔴 Красное/чёрное — выплата 2×\n"
            "🟢 Зеро/точное число — выплата 36× "
            "(включая ставку).",
            menu()
        )

    elif txt.startswith("/balance"):
        send(chat, f"🪙 Баланс: {balances[uid]} монет", menu())

    elif txt.startswith("/menu"):
        send(chat, "👑 IMPERIUM CASINO", menu())

    elif txt.startswith("/roulette"):
        p = txt.split()

        if len(p) == 2 and p[1].isdigit():
            amount = int(p[1])

            if amount < 1:
                send(chat, "❌ Ставка должна быть больше нуля.", menu())
            else:
                send(chat, "Выбери тип ставки:", types(amount))
        else:
            send(chat, "Пример: /roulette 100", menu())


def callback(q):
    d = q.get("data", "")
    m = q.get("message", {})
    chat = m.get("chat", {}).get("id")
    mid = m.get("message_id")
    uid = q.get("from", {}).get("id")

    answer(q["id"])

    if chat is None or uid is None:
        return

    balances.setdefault(uid, 1000)

    if d == "menu":
        edit(chat, mid, "👑 IMPERIUM CASINO", menu())

    elif d == "play":
        edit(chat, mid, "🎰 Выбери размер ставки:", bets())

    elif d == "bal":
        edit(chat, mid, f"🪙 Баланс: {balances[uid]} монет", menu())

    elif d == "hist":
        h = histories.get(uid, [])
        text = (
            "📜 Последние игры\n\n"
            + ("\n".join("• " + x for x in h) if h else "Пока игр нет.")
        )
        edit(chat, mid, text, menu())

    elif d == "bonus":
        today = time.strftime("%Y-%m-%d", time.gmtime())

        if bonuses.get(uid) == today:
            edit(
                chat, mid,
                "🎁 Бонус уже получен. Возвращайся завтра!",
                menu()
            )
        else:
            bonuses[uid] = today
            balances[uid] += 250
            save()
            edit(
                chat, mid,
                f"🎁 Получено +250 монет!\n"
                f"🪙 Баланс: {balances[uid]}",
                menu()
            )

    elif d == "custom":
        edit(
            chat, mid,
            "✍️ Отправь сумму командой, например /roulette 75",
            menu()
        )

    elif d.startswith("bet:"):
        b = int(d.split(":")[1])

        if b <= balances[uid]:
            edit(chat, mid, f"🎰 Ставка {b} монет. Выбери тип:", types(b))
        else:
            edit(
                chat, mid,
                f"❌ Баланс только {balances[uid]} монет.",
                bets()
            )

    elif d.startswith("num:"):
        b = int(d.split(":")[1])
        edit(
            chat, mid,
            f"🎯 Выбери число для ставки {b}:",
            number_buttons(b)
        )

    elif d.startswith("pick:"):
        _, b, n = d.split(":")
        spin(chat, uid, int(b), "number", int(n), mid)

    elif d.startswith("spin:"):
        _, b, k = d.split(":")
        spin(chat, uid, int(b), k, None, mid)


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"IMPERIUM ROULETTE OK")

    def log_message(self, *args):
        pass


def main():
    if not TOKEN:
        print("ОШИБКА: BOT_TOKEN не найден", flush=True)
        return

    load()

    threading.Thread(
        target=lambda: HTTPServer(
            ("0.0.0.0", PORT), Health
        ).serve_forever(),
        daemon=True
    ).start()

    print(f"IMPERIUM ROULETTE запущен на порту {PORT}", flush=True)

    offset = 0

    while True:
        try:
            for u in api(
                "getUpdates",
                {"offset": offset, "timeout": 20}
            ) or []:
                offset = u["update_id"] + 1

                try:
                    if "message" in u:
                        message(u["message"])
                    elif "callback_query" in u:
                        callback(u["callback_query"])
                except Exception as e:
                    print("Update error:", e, flush=True)

        except Exception as e:
            print("Telegram error:", e, flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
