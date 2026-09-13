import threading
import time
from web import app
from telegram_bot import start_telegram_bot
from market import get_live_market_data
from strategy import analyze_market_for_dip

def run_flask():
    # Flask uygulamasını Render'ın istediği portta başlat
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

def run_telegram_listener():
    # Telegram komut dinleyicisini başlat
    try:
        start_telegram_bot()
    except Exception as e:
        print(f"Telegram Bot Başlatma Hatası: {e}")

def trading_loop():
    print("🚀 Otonom Al-Sat Döngüsü Başlatıldı.")
    symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
    while True:
        try:
            for symbol in symbols:
                action, price, rsi, reason = analyze_market_for_dip(symbol)
                print(f"[{symbol}] İşlem: {action} | Fiyat: {price} | RSI: {rsi} | Sebep: {reason}")
        except Exception as e:
            print(f"İşlem döngüsü hatası: {e}")
        time.sleep(30)

if __name__ == "__main__":
    print("🌟 Apex Bot Sistemleri Birlikte Başlatılıyor...")

    # 1. Flask Web Sunucusunu Arka Planda (Thread) Başlat
    t_flask = threading.Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()

    # 2. Telegram Komut Dinleyicisini Arka Planda (Thread) Başlat
    t_telegram = threading.Thread(target=run_telegram_listener)
    t_telegram.daemon = True
    t_telegram.start()

    # 3. Ana İşlemde Al-Sat Döngüsünü Çalıştır
    trading_loop()
