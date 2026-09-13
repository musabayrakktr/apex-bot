import os
import threading
import time
from web import app
from telegram_bot import start_telegram_bot
from strategy import analyze_market_for_dip

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_telegram():
    try:
        start_telegram_bot()
    except Exception as e:
        print(f"Telegram Thread Hatası: {e}")

def trading_loop():
    print("🚀 Otonom Al-Sat Döngüsü Başlatıldı.")
    symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
    while True:
        try:
            for symbol in symbols:
                analyze_market_for_dip(symbol)
        except Exception as e:
            print(f"Döngü hatası: {e}")
        time.sleep(30)

if __name__ == "__main__":
    print("🌟 Apex Bot Polling Sistemine Geri Döndü...")

    # 1. Telegram botunu arka planda başlat
    t_telegram = threading.Thread(target=run_telegram)
    t_telegram.daemon = True
    t_telegram.start()

    # 2. Al-sat döngüsünü arka planda başlat
    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # 3. Flask'ı ana thread'de çalıştır
    run_flask()
