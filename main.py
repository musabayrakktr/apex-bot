import os
import time
import threading
import telebot
from flask import Flask
from market import get_live_market_data
from strategy import analyze_market_for_dip

TELEGRAM_TOKEN = "8851186730:AAEChJwI1Uj7J0xfed-fZ4pEiyzVfyFZhcA"
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Apex Bot 7/24 Aktif ve Çalışıyor! 🚀"

@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    bot.reply_to(message, "🚀 *APEX BOT AKTİF VE DEVREDE!*\nSol menüden dilediğin komutu seçebilirsin kanka!", parse_mode="Markdown")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    cevap = (
        "💼 *APEX VIRTUAL CÜZDAN*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💵 Bakiye: `$1,250.00`\n"
        "🪙 Varlık: `₺42,850.50`"
    )
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['analiz'])
def send_analysis(message):
    veriler = get_live_market_data()
    cevap = "📊 *CANLI PİYASA ANALİZİ*\n━━━━━━━━━━━━━━━━━━━\n"
    for item in veriler[:3]:
        cevap += f"🪙 {item.get('parite', 'SOL/USDT')} - Fiyat: {item.get('fiyat', '100')}\n"
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['rapor'])
def send_report(message):
    bot.reply_to(message, "📋 *SİSTEM RAPORU*\n🟢 Render Sunucusu uyanık ve çalışıyor.", parse_mode="Markdown")

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

def run_polling():
    print("🤖 Telegram Bot Polling Döngüsü Başlatıldı...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🌟 Apex Bot Sıfırdan Temiz Kurulum ile Başlatılıyor...")

    # 1. Al-sat döngüsünü arka planda başlat
    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # 2. Telegram dinleme döngüsünü arka planda başlat
    t_telegram = threading.Thread(target=run_polling)
    t_telegram.daemon = True
    t_telegram.start()

    # 3. Flask sunucusunu başlat (Render uyumasın diye)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
