import os
import threading
from telegram_bot import handle_message, set_telegram_commands
from web import app
import time
import json
import urllib.request
from config import TELEGRAM_TOKEN

def telegram_listener():
    """Telegram mesajlarını arka planda kesintisiz dinleyen döngü"""
    offset = 0
    # Eski çakışan webhook'ları temizle
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except Exception:
        pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=10"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as res:
                data = json.loads(res.read().decode())
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            msg = update["message"]
                            text = msg.get("text", "").strip()
                            chat_id = msg.get("chat", {}).get("id")
                            if text and chat_id:
                                handle_message(text, chat_id)
        except Exception:
            time.sleep(2)

if __name__ == '__main__':
    try:
        set_telegram_commands()
    except Exception:
        pass
        
    # 1. Telegram dinleyicisini arka plan thread'inde başlat
    t_tele = threading.Thread(target=telegram_listener, daemon=True)
    t_tele.start()
    
    # 2. Render portunu dinleyen Flask web sunucusunu ana kanalda başlat
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
