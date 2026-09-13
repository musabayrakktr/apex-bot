import os
import time
import threading
from web import app
from strategy import analyze_market_for_dip
from trader import execute_buy_order
from telegram_bot import set_telegram_commands

# Takip edilen coinler
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

def auto_trading_loop():
    """Arka planda piyasayı sürekli tarayan ve alım tetikleyen döngü"""
    time.sleep(5)  # Sunucu açılırken 5 sn bekle
    print("🤖 APEX Oto Alım-Satım Motoru Başlatıldı...")
    
    # Telegram menü komutlarını ayarla
    try:
        set_telegram_commands()
    except Exception as e:
        print(f"Telegram set commands hatası: {e}")

    while True:
        try:
            for symbol in SYMBOLS:
                should_buy, price, rsi, reason = analyze_market_for_dip(symbol)
                
                if should_buy:
                    print(f"🎯 Dip Yakalandı ({symbol})! Alım yapılıyor...")
                    execute_buy_order(symbol, price, rsi)
                    # Test modunda her 30 saniyede bir alım yapmaması için kısa bekleme
                    time.sleep(15)
                    break
        except Exception as e:
            print(f"Döngü hatası: {e}")
            
        time.sleep(10)  # Her 10 saniyede bir tbox taraması yapar

if __name__ == '__main__':
    # Alım motorunu arka planda (Thread) başlat
    trading_thread = threading.Thread(target=auto_trading_loop, daemon=True)
    trading_thread.start()
    
    # Flask Web Sunucusunu çalıştır
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
