import time
import threading
from web import app
from strategy import analyze_market_for_dip

def run_flask():
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

def trading_loop():
    print("🚀 Otonom Al-Sat Döngüsü Başlatıldı.")
    symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
    while True:
        try:
            for symbol in symbols:
                analyze_market_for_dip(symbol)
        except Exception as e:
            print(f"İşlem döngüsü hatası: {e}")
        time.sleep(30)

if __name__ == "__main__":
    print("🌟 Apex Bot Webhook Mimarisiyle Başlatılıyor...")

    # Al-sat döngüsünü arka planda başlat
    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # Flask web sunucusunu ana thread'de başlat
    run_flask()
