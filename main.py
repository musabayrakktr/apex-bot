import os
import threading
import time
from config import SYMBOLS
from strategy import analyze_market_for_dip
from telegram_bot import bot, trading_active
from web import app

def trading_loop():
    print("🚀 Otonom RSI Dip ve Al-Sat Döngüsü Başlatıldı.")
    while True:
        try:
            if trading_active:
                for symbol in SYMBOLS:
                    action, price, rsi, message = analyze_market_for_dip(symbol)
                    print(f"[{symbol}] İşlem: {action} | Fiyat: ${price} | RSI: {rsi} | Durum: {message}")
                    if action in ["BUY", "SELL"]:
                        print(f"⚡ KRİTİK SİNYAL: {symbol} -> {action} ({message})")
        except Exception as e:
            print(f"Döngü hatası: {e}")
        time.sleep(30)

def run_telegram():
    print("🤖 Telegram Bot dinlemeye başladı...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    print("🌟 Apex Bot Strateji Entegrasyonlu Başlatılıyor...")

    # Arka plan ticaret motoru
    t_trade = threading.Thread(target=trading_loop, daemon=True)
    t_trade.start()

    # Arka plan Telegram bot dinleyicisi
    t_tg = threading.Thread(target=run_telegram, daemon=True)
    t_tg.start()

    # Flask Web Sunucusu
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
