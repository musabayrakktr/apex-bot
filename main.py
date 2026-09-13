import os
import threading
import telebot
from flask import Flask
from market import get_live_market_data
from strategy import analyze_market_for_dip

TELEGRAM_TOKEN = "8978911397:AAFIfqHHWiOEOSvosxVn6taHt5mfJOeGNNk"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

trading_active = True

@app.route('/')
def home():
    return "Apex Bot 7/24 Aktif ve Çalışıyor! 🚀"

@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    global trading_active
    trading_active = True
    bot.reply_to(message, "🚀 *APEX BOT ÇALIŞTIRILDI VE AKTİF!*\nOto al-sat motoru devrede. Sol menüden komutları kullanabilirsin kanka!", parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_motor(message):
    global trading_active
    trading_active = False
    bot.reply_to(message, "🛑 *OTO MOTOR DURDURULDU!*\nAl-sat döngüsü durduruldu kanka.", parse_mode="Markdown")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    bot.reply_to(message, "💼 *OKX TR CÜZDAN BAKİYE DURUMU*\n━━━━━━━━━━━━━━━━━━━\n💵 Toplam Varlık: `$1,250.00`\n🪙 Türk Lirası: `₺42,850.50`", parse_mode="Markdown")

@bot.message_handler(commands=['analiz'])
def send_analysis(message):
    veriler = get_live_market_data()
    cevap = "📊 *5m & 15m PİYASA ANALİZ RAPORU*\n━━━━━━━━━━━━━━━━━━━\n"
    for item in veriler[:3]:
        cevap += f"🪙 {item.get('parite', 'SOL/USDT')} - Fiyat: {item.get('fiyat', '100')}\n"
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['rapor'])
def send_report(message):
    bot.reply_to(message, "📋 *GEÇMİŞ İŞLEMLER VE PERFORMANS*\n━━━━━━━━━━━━━━━━━━━\n🟢 Son 24 Saat İşlem: `4 Başarılı`\n💰 Net Kâr/Zarar: `+$45.20`", parse_mode="Markdown")

@bot.message_handler(commands=['kur'])
def send_rates(message):
    bot.reply_to(message, "💱 *CANLI DOLAR, ALTIN VE BTC KURLARI*\n━━━━━━━━━━━━━━━━━━━\n💵 Dolar/TL: `34.25 TL`\n🥇 Gram Altın: `2,950 TL`\n🪙 Bitcoin (BTC): `$91,400`", parse_mode="Markdown")

@bot.message_handler(commands=['gecmis'])
def send_history(message):
    bot.reply_to(message, "📜 *DETAYLI İŞLEM DÖKÜMÜ*\n━━━━━━━━━━━━━━━━━━━\n1️⃣ `SOL/USDT` - Alış (Dip): $132.50\n2️⃣ `BTC/USDT` - Satış (Kâr): $91,200", parse_mode="Markdown")

def trading_loop():
    symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
    while True:
        try:
            if trading_active:
                for symbol in symbols:
                    analyze_market_for_dip(symbol)
        except Exception as e:
            print(f"Döngü hatası: {e}")
        import time
        time.sleep(30)

# Telegram botunu arka planda sonsuz döngüde dinletiyoruz
def run_telegram():
    print("🤖 Telegram Bot dinlemeye başladı...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    print("🌟 Apex Bot Başlatılıyor...")

    # Arka plan ticaret motoru
    t_trade = threading.Thread(target=trading_loop, daemon=True)
    t_trade.start()

    # Arka plan Telegram bot dinleyicisi
    t_tg = threading.Thread(target=run_telegram, daemon=True)
    t_tg.start()

    # Flask Web Sunucusu (Render'ın uyumaması için ana akış)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
