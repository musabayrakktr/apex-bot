import telebot
from config import TELEGRAM_TOKEN
from market import get_okx_usdt_balance, get_live_finans_data

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    welcome_text = (
        "🚀 *APEX TRADING BOT - CANLI OKX TR* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Modüler sistem ve canlı bakiye entegrasyonu aktif!\n\n"
        "💼 `/cuzdan` - OKX TR Canlı Cüzdan Durumu\n"
        "💱 `/kur` - Canlı Dolar ve BTC Kurları"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    try:
        # Doğrudan OKX'ten canlı bakiye ve kur çekiliyor
        usdt_bakiye = get_okx_usdt_balance()
        btc, dolar = get_live_finans_data()
        try_bakiye = usdt_bakiye * dolar
        
        cevap = (
            "💼 *OKX TR CANLI CÜZDAN DURUMU*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Canlı Varlık: `${usdt_bakiye:,.2f} USDT`\n"
            f"🪙 Türk Lirası Karşılığı: `₺{try_bakiye:,.2f} TRY`\n"
            f"📊 Anlık OKX Kur: `{dolar:.2f} TL`"
        )
        bot.send_message(message.chat.id, cevap, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Cüzdan okunurken hata oluştu: {e}")

@bot.message_handler(commands=['kur'])
def send_rates(message):
    btc, dolar = get_live_finans_data()
    bot.send_message(message.chat.id, f"💱 *CANLI OKX KURLARI*\n━━━━━━━━━━━━━━━━━━━\n💵 Dolar/TL: `{dolar:.2f} TL`\n🪙 Bitcoin (BTC): `${btc:,.2f}`", parse_mode="Markdown")
