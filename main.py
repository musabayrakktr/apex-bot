import os
import time
import json
import urllib.request
import threading
from web import app
from strategy import analyze_market_for_dip
from trader import execute_buy_order
from telegram_bot import set_telegram_commands, handle_message
from config import TELEGRAM_TOKEN

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

def telegram_polling_loop():
    """Telegram gelen mesajları 7/24 dinleyen döngü"""
    offset = 0
    print("🤖 Telegram Dinleyici Başlatıldı...")
    try:
        set_telegram_commands()
    except Exception as e:
        print(f"Set commands hatası: {e}")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=5"
            req = urllib.request.Request(url)
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read().decode('utf-8'))

            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        text = update["message"]["text"]
                        chat_id = update["message"]["chat"]["id"]
                        handle_message(text, chat_id)
        except Exception as e:
            time.sleep(2)
        time.sleep(1)

def auto_trading_loop():
    """Piyasayı sürekli tarayan ve alım tetikleyen otomatik motor"""
    time.sleep(5)
    print("📈 Oto Alım-Satım Motoru Başlatıldı...")
    while True:
        try:
            for symbol in SYMBOLS:
                should_buy, price, rsi, reason = analyze_market_for_dip(symbol)
                if should_buy:
                    print(f"🎯 Dip Yakalandı ({symbol})! Alım yapılıyor...")
                    execute_buy_order(symbol, price, rsi)
                    time.sleep(20)  # Üst üste alım yapmaması için bekleme
                    break
        except Exception as e:
            print(f"Oto alım hatası: {e}")
        time.sleep(10)

if __name__ == '__main__':
    # 1. Telegram Mesaj Dinleyici Thread
    t1 = threading.Thread(target=telegram_polling_loop, daemon=True)
    t1.start()

    # 2. Oto Alım-Satım Motoru Thread
    t2 = threading.Thread(target=auto_trading_loop, daemon=True)
    t2.start()

    # 3. Web Sunucusu (Main Process)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
