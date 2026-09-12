import os
import threading
import time
import json
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
    except: 
        pass
        
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.loads(response.read().decode())
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            msg = update["message"]
                            text = msg.get("text", "").strip()
                            chat_id = msg.get("chat", {}).get("id")
                            if text and chat_id:
                                handle_message(text, chat_id)
        except Exception as e:
            print(f"Polling hatası: {e}")
            time.sleep(3)

@app.route('/')
def home():
    return render_dashboard()

if __name__ == '__main__':
    t = threading.Thread(target=telegram_polling_listener, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
