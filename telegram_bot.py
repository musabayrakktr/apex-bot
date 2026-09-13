import os
import time
import telebot
from market import get_live_market_data

TELEGRAM_TOKEN = "8851186730:AAEChJwI1Uj7J0xfed-fZ4pEiyzVfyFZhcA"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

def start_telegram_bot():
    print("🤖 Telegram Bot Long Polling ile başlatılıyor...")
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"Telegram Bot Polling Hatası: {e}")
            time.sleep(5)
