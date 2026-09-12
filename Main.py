import os
import threading
import time
import urllib.request
from flask import Flask
from config import TELEGRAM_TOKEN
from telegram_bot import handle_message
from web import render_dashboard

app = Flask(__name__)

def telegram_polling_listener():
    offset = 0
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                import json
                data = json.loads(response.read().decode())
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            handle_message(update["message"].get("text", "").strip(), update["message"]["chat"].get("id"))
        except: time.sleep(3)

@app.route('/')
def home():
    return render_dashboard()

if __name__ == '__main__':
    # Arka planda Telegram dinleyicisini başlat
    threading.Thread(target=telegram_polling_listener, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
