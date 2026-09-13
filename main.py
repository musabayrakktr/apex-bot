import os
import threading
import time
from web import app
from telegram_bot import start_telegram_bot
from market import get_live_market_data
from strategy import analyze_market_for_dip

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_telegram():
    print("🤖 Telegram Bot thread başlatılıyor...")
    try:
        start_telegram_bot()
    except Exception as e:
        print(f"Telegram Thread Hatası: {e}")

if __name__ == "__main__":
    print("🌟 Apex Bot Başlatılıyor...")

    # Telegram botunu bağımsız bir thread'de başlat
    t_telegram = threading.Thread(target=run_telegram)
    t_telegram.daemon = True
    t_telegram.start()

    # Al-sat döngüsünü ayrı bir thread'e al ki sistemi bloklamasın
    def trading_loop():
        symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
        while True:
            try:
                for symbol in symbols:
                    analyze_market_for_dip(symbol)
            except Exception as e:
                print(f"Döngü hatası: {e}")
            time.sleep(30)

    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # Flask'ı ana thread'de çalıştır (Render portu bekler)
    run_flask()
