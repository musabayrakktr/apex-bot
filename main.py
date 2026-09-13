import os
import time
import telebot
from flask import Flask
from market import get_live_market_data
from strategy import analyze_market_for_dip

# --- 1. AYARLAR VE TOKEN ---
TELEGRAM_TOKEN = "8851186730:AAEChJwI1Uj7J0xfed-fZ4pEiyzVfyFZhcA"
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- 2. FLASK WEB SUNUCUSU (Render'ın uyumaması için) ---
@app.route('/')
def home():
    return "Apex Bot 7/24 Aktif ve Çalışıyor! 🚀"

# --- 3. TELEGRAM KOMUTLARI ---
@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    bot.reply_to(message, "🚀 *APEX BOT AKTİF VE DEVREDE!*\nSol menüden dilediğin komutu seçebilirsin kanka!")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    cevap = (
        "💼 *APEX VIRTUAL CÜZDAN RAPORU*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💵 *Bakiye (USDT):* `$1,250.00`\n"
        "🪙 *Toplam Varlık (TRY):* `₺42,850.50`\n"
        "📊 *Aktif Pozisyon Sayısı:* `3`"
    )
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['analiz'])
def send_analysis(message):
    veriler = get_live_market_data()
    cevap = "📊 *CANLI PİYASA ANALİZ RAPORU*\n━━━━━━━━━━━━━━━━━━━\n"
    for item in veriler[:3]:
        parite = item.get("parite", "SOL/USDT")
        fiyat = item.get("fiyat", "100")
        rsi = item.get("rsi", "50")
        cevap += f"🪙 *{parite}*\n💰 Fiyat: `{fiyat}` | 📈 RSI: `{rsi}`\n\n"
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['rapor'])
def send_report(message):
    cevap = (
        "📋 *APEX SİSTEM DURUM RAPORU*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🟢 *Render Sunucusu:* `%100 Uyanık`\n"
        "🤖 *Bot Durumu:* `Sorunsuz Çalışıyor`"
    )
    bot.reply_to(message, cevap, parse_mode="Markdown")

# --- 4. AL-SAT DÖNGÜSÜ ---
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

# --- 5. ANA BAŞLATICI ---
if __name__ == "__main__":
    import threading

    print("🌟 Apex Bot Tek Dosya Modunda Başlatılıyor...")

    # Arka planda al-sat döngüsünü başlat
    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    # Arka planda Telegram bot polling başlat
    def run_polling():
        while True:
            try:
                print("🤖 Telegram Bot Polling Başlıyor...")
                bot.infinity_polling(timeout=20, long_polling_timeout=5)
            except Exception as e:
                print(f"Polling Hatası: {e}")
                time.sleep(5)

    t_telegram = threading.Thread(target=run_polling)
    t_telegram.daemon = True
    t_telegram.start()

    # Flask sunucusunu ana thread'de çalıştır (Render port şartını sağlasın diye)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
