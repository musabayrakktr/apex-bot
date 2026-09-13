import time
from threading import Thread
from market import get_live_market_data
from strategy import analyze_market_for_dip
from telegram_bot import send_telegram, start_telegram_bot
from web import app

def trading_loop():
    print("🚀 APEX Trading Loop Başlatıldı...")
    # Sunucu kalkar kalkmaz Telegram'a test mesajı salla
    try:
        send_telegram("⚡ APEX BOT SİSTEMİ AKTİF! Dip Taraması Başlatıldı.")
    except Exception as e:
        print(f"Telegram Başlangıç Hatası: {e}")

    while True:
        try:
            symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
            for symbol in symbols:
                buy_signal, price, rsi, reason = analyze_market_for_dip(symbol)
                
                if buy_signal:
                    msg = (
                        f"🚀 *ALIM İŞLEMİ GERÇEKLEŞTİ!*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 *Parite:* `{symbol}`\n"
                        f"💰 *Fiyat:* `${price}`\n"
                        f"📊 *RSI:* `{rsi:.1f}`\n"
                        f"📝 *Sebep:* {reason}\n\n"
                        f"🤖 *OKX TR Otomatik Emir Verildi.*"
                    )
                    print(f" Telegram'a gönderiliyor: {symbol}")
                    send_telegram(msg)
                    
        except Exception as e:
            print(f"Döngü hatası: {e}")
            
        time.sleep(15) # 15 saniyede bir tara ve at

if __name__ == "__main__":
    # Telegram Botunu Dinlemeye Başla
    t_bot = Thread(target=start_telegram_bot)
    t_bot.daemon = True
    t_bot.start()

    # Alım Döngüsünü Başlat
    t_trade = Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # Web Sunucusunu Başlat
    app.run(host="0.0.0.0", port=10000)
