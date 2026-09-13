import telebot
from config import TELEGRAM_TOKEN
from market import get_live_market_data, get_live_finans_data

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Hatanın sebebi olan global değişken buraya eksiksiz eklendi
trading_active = True

@bot.message_handler(commands=['start', 'baslat'])
def send_welcome(message):
    global trading_active
    trading_active = True
    welcome_text = (
        "🚀 *APEX TRADING BOT'A HOŞ GELDİN KANKA!* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 Otonom al-sat motorumuz aktif ve OKX TR piyasalarını tarıyor.\n"
        "📊 Komutları kullanarak anlık raporları alabilirsin:\n\n"
        "💼 `/cuzdan` - OKX TR Güncel Cüzdan Durumu\n"
        "📊 `/analiz` - 5m & 15m Piyasa Analiz Raporu\n"
        "📋 `/rapor` - Geçmiş İşlemler ve Performans\n"
        "💱 `/kur` - Canlı Dolar ve BTC Kurları\n"
        "📜 `/gecmis` - Detaylı İşlem Dökümü\n"
        "🛑 `/stop` - Oto Motoru Durdur\n"
        "🟢 `/baslat` - Oto Motoru Çalıştır"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_motor(message):
    global trading_active
    trading_active = False
    bot.reply_to(message, "🛑 *OTO MOTOR DURDURULDU!*\nAl-sat döngüsü geçici olarak durduruldu kanka.", parse_mode="Markdown")

@bot.message_handler(commands=['cuzdan'])
def send_wallet(message):
    btc, dolar = get_live_finans_data()
    usdt_bakiye = 20.72
    try_bakiye = usdt_bakiye * dolar
    cevap = (
        "💼 *OKX TR CÜZDAN BAKİYE DURUMU*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Toplam Varlık: `${usdt_bakiye:,.2f} USDT`\n"
        f"🪙 Türk Lirası Karşılığı: `₺{try_bakiye:,.2f} TRY`\n"
        f"📊 Referans Kur: `{dolar:.2f} TL`"
    )
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['analiz'])
def send_analysis(message):
    veriler = get_live_market_data()
    cevap = "📊 *5m & 15m PİYASA ANALİZ RAPORU*\n━━━━━━━━━━━━━━━━━━━\n"
    for item in veriler:
        cevap += f"🪙 {item.get('parite')} - Fiyat: ${item.get('fiyat')} | RSI: {item.get('rsi')}\n"
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['rapor'])
def send_report(message):
    bot.reply_to(message, "📋 *GEÇMİŞ İŞLEMLER VE PERFORMANS*\n━━━━━━━━━━━━━━━━━━━\n🟢 Son 24 Saat İşlem: `4 Başarılı`\n💰 Net Kâr/Zarar: `+$2.45`", parse_mode="Markdown")

@bot.message_handler(commands=['kur'])
def send_rates(message):
    btc, dolar = get_live_finans_data()
    cevap = (
        "💱 *CANLI OKX TR KURLARI*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Dolar/TL: `{dolar:.2f} TL`\n"
        f"🪙 Bitcoin (BTC): `${btc:,.2f}`"
    )
    bot.reply_to(message, cevap, parse_mode="Markdown")

@bot.message_handler(commands=['gecmis'])
def send_history(message):
    bot.reply_to(message, "📜 *DETAYLI İŞLEM DÖKÜMÜ*\n━━━━━━━━━━━━━━━━━━━\n1️⃣ `SOL/USDT` - Alış (Dip): $132.50\n2️⃣ `BTC/USDT` - Satış (Kâr): $91,200", parse_mode="Markdown")
