import time
from threading import Thread
from market import get_live_market_data
from strategy import analyze_market_for_dip
from telegram_bot import send_telegram, start_telegram_bot
from web import app

def trading_loop():
    print("🚀 APEX Otonom Al-Sat Döngüsü Başlatıldı...")
    try:
        send_telegram("🟢 *APEX BOT AKTİF!*\nGerçek RSI Dip Stratejisi ve Al-Sat Modülü Devrede.")
    except Exception as e:
        print(f"Telegram Başlangıç Hatası: {e}")

    while True:
        try:
            symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
            for symbol in symbols:
                action, price, rsi, reason = analyze_market_for_dip(symbol)
                
                if action == "BUY":
                    msg = (
                        f"🚀 *ALIM İŞLEMİ GERÇEKLEŞTİ!*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 *Parite:* `{symbol}`\n"
                        f"💰 *Giriş Fiyatı:* `${price}`\n"
                        f"📊 *RSI:* `{rsi:.1f}`\n"
                        f"📝 *Sebep:* {reason}\n\n"
                        f"🎯 *Hedef:* %+2.5 Kâr | *Stop:* %-1.5"
                    )
                    send_telegram(msg)
                    
                elif action == "SELL":
                    msg = (
                        f"💰 *SATIŞ (KÂR/ZARAR) KAPANIŞI!*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 *Parite:* `{symbol}`\n"
                        f"💵 *Çıkış Fiyatı:* `${price}`\n"
                        f"📊 *RSI:* `{rsi:.1f}`\n"
                        f"📝 *Sonuç:* {reason}\n\n"
                        f"✅ *İşlem Başarıyla Kapatıldı.*"
                    )
                    send_telegram(msg)
                    
        except Exception as e:
            print(f"Döngü hatası: {e}")
            
        time.sleep(30) # 30 saniyede bir piyasayı tara

if __name__ == "__main__":
    t_bot = Thread(target=start_telegram_bot)
    t_bot.daemon = True
    t_bot.start()

    t_trade = Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    app.run(host="0.0.0.0", port=10000)
