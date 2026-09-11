import os
import time
import requests
import ccxt
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. AYARLAR & PARİTELER ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

OKX_API_KEY = os.environ.get("OKX_API_KEY")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE")

# Genişletilmiş Parite Listesi
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT']

# Dinamik Bot Parametreleri
BUY_RSI_THRESHOLD = 30.0
TAKE_PROFIT_PCT = 3.5
STOP_LOSS_PCT = 2.5
TRAILING_STOP_TRIGGER = 2.0
TRAILING_STOP_DROP = 1.0

# Borsa Bağlantısı
exchange = ccxt.okx({
    'apiKey': OKX_API_KEY,
    'secret': OKX_SECRET_KEY,
    'password': OKX_PASSPHRASE,
    'enableRateLimit': True,
})

# Hafıza Durumları
last_signals = {s: "⚪ BEKLE" for s in SYMBOLS}
historical_rsi = {s: [] for s in SYMBOLS}
active_positions = {}

# --- 2. TEKNİK İNDİKATÖR VE TAHMİN FONKSİYONLARI ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def predict_trend(symbol_rsi_history):
    if len(symbol_rsi_history) < 3:
        return "🔮 Yeterli veri yok, yön tespiti bekleniyor."
    rsi_diff = symbol_rsi_history[-1] - symbol_rsi_history[-3]
    if symbol_rsi_history[-1] <= 35:
        return f"🔮 DİP BÖLGESİ! Önümüzdeki 15-30 dk içinde tepki yükselişi gelebilir."
    elif rsi_diff < -4:
        return f"🔮 DÜŞÜŞ İVMELENİYOR! Önümüzdeki 15-30 dk içinde RSI <= {BUY_RSI_THRESHOLD} dip seviyesine ulaşma ihtimali yüksek."
    elif rsi_diff > 4:
        return f"🔮 YÜKSELİŞ İVMESİ! Fiyat yukarı hareketini sürdürüyor."
    else:
        return "🔮 YATAY SEYİR! Piyasada belirgin kırılım beklenmiyor."

def send_telegram_msg(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Telegram Gönderim Hatası: {e}")

# --- 3. TELEGRAM KOMUTLARI ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 **APEX YAYINDA!** Yapay zeka tahmin motoru ve dinamik komutlar aktif kanka.")

async def cmd_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📡 **APEX CANLI PİYASA & TAHMİN RAPORU**\n\n"
    for s in SYMBOLS:
        try:
            ticker = exchange.fetch_ticker(s)
            ohlcv = exchange.fetch_ohlcv(s, timeframe='15m', limit=20)
            closes = [x[4] for x in ohlcv]
            rsi = calculate_rsi(closes)
            historical_rsi[s].append(rsi)
            if len(historical_rsi[s]) > 5:
                historical_rsi[s].pop(0)
            
            prediction = predict_trend(historical_rsi[s])
            msg += f"🪙 **{s.split('/')[0]}:** `{ticker['last']:.2f}` $ | RSI: `{rsi:.1f}`\n{prediction}\n\n"
        except Exception as e:
            msg += f"⚠️ {s} verisi çekilemedi.\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_cuzdan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balance = exchange.fetch_balance()
        usdt_free = balance['total'].get('USDT', 0.0)
        try:
            try_free = balance['total'].get('TRY', 0.0)
        except:
            try_free = 0.0
        await update.message.reply_text(f"💼 **OKX CÜZDAN BAKİYESİ**\n\nUSDT: `{usdt_free:.4f}`\nTRY: `{try_free:.2f}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Cüzdan bilgisi çekilemedi: {e}")

async def cmd_set_rsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BUY_RSI_THRESHOLD
    try:
        val = float(context.args[0])
        BUY_RSI_THRESHOLD = val
        await update.message.reply_text(f"✅ Alım RSI eşiği `{BUY_RSI_THRESHOLD}` olarak güncellendi kanka!")
    except:
        await update.message.reply_text("⚠️ Kullanım: `/set_rsi 28` şeklinde sayı gir kanka.", parse_mode="Markdown")

async def cmd_set_tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TAKE_PROFIT_PCT
    try:
        val = float(context.args[0])
        TAKE_PROFIT_PCT = val
        await update.message.reply_text(f"✅ Take-Profit hedefi `%{TAKE_PROFIT_PCT}` olarak güncellendi kanka!")
    except:
        await update.message.reply_text("⚠️ Kullanım: `/set_tp 4.0` şeklinde sayı gir kanka.", parse_mode="Markdown")

async def cmd_set_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global STOP_LOSS_PCT
    try:
        val = float(context.args[0])
        STOP_LOSS_PCT = val
        await update.message.reply_text(f"✅ Stop-Loss limiti `%{STOP_LOSS_PCT}` olarak güncellendi kanka!")
    except:
        await update.message.reply_text("⚠️ Kullanım: `/set_sl 2.0` şeklinde sayı gir kanka.", parse_mode="Markdown")

# --- 4. ANA DÖNGÜ & BOT KURULUMU ---
def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Bot token bulunamadı!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("analiz", cmd_analiz))
    app.add_handler(CommandHandler("cuzdan", cmd_cuzdan))
    app.add_handler(CommandHandler("set_rsi", cmd_set_rsi))
    app.add_handler(CommandHandler("set_tp", cmd_set_tp))
    app.add_handler(CommandHandler("set_sl", cmd_set_sl))

    print("APEX Bot Başlatılıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
