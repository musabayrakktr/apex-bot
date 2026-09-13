import telebot
from config import TELEGRAM_TOKEN, ADMIN_ID
from market import get_okx_usdt_balance, get_live_finans_data

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def is_admin(message):
    """Gelen mesajın sahibi sen misin diye kontrol eder."""
    return message.from_user.id == ADMIN_ID

@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    if not is_admin(message):
        bot.send_message(message.chat.id, "⛔ Bu botu kullanma yetkin yok kanka!")
        return
        
    welcome_text = (
        "🚀 *APEX TRADING BOT - GÜVENLİ SÜRÜM* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Admin kimliğin doğrulandı! Canlı bakiye ve al-sat modülü aktif.\n\n"
        "💼 `/cuzdan` - OKX TR Canlı Cüzdan Durumu\n"
        "💱 `/kur` - Canlı Dolar ve BTC Kurları"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    if not is_admin(message):
        bot.send_message(message.chat.id, "⛔ Bu komutu kullanmaya yetkin yok!")
        return
        
    try:
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
    if not is_admin(message):
        return
    btc, dolar = get_live_finans_data()
    bot.send_message(message.chat.id, f"💱 *CANLI OKX KURLARI*\n━━━━━━━━━━━━━━━━━━━\n💵 Dolar/TL: `{dolar:.2f} TL`\n🪙 Bitcoin (BTC): `${btc:,.2f}`", parse_mode="Markdown")
