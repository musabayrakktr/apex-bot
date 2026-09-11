import os
import time
import asyncio
import threading
import requests
import ccxt
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. SIFIR BAĞIMLILIK HTTP DİNLEYİCİSİ (RENDER İÇİN) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"APEX Bot Canli!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- 2. BOT AYARLARI & PARİTELER ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

OKX_API_KEY = os.environ.get("OKX_API_KEY")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE")

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT']

BUY_RSI_THRESHOLD = 30.0
TAKE_PROFIT_PCT = 3.5
STOP_LOSS_PCT = 2.5

exchange = ccxt.okx({
    'apiKey': OKX_API_KEY,
    'secret': OKX_SECRET_KEY,
    'password': OKX_PASSPHRASE,
    'enableRateLimit': True,
})

historical_rsi = {s: [] for s in SYMBOLS}

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
        return "🔮 Yön tespiti bekleniyor..."
    rsi_diff = symbol_rsi_history[-1] - symbol_rsi_history[-3]
    if symbol_rsi_history[-1] <= 35:
        return "🔮 DİP BÖLGESİ! Tepki yükselişi gelebilir."
    elif rsi_diff < -4:
        return f"🔮 DÜŞÜŞ İVMELENİYOR! RSI <= {BUY_RSI_THRESHOLD} olma ihtimali yüksek."
    elif rsi_diff > 4:
        return "🔮 YÜKSELİŞ İVMESİ! Fiyat yukarı gidiyor."
    else:
        return "🔮 YATAY SEYİR! Sakin piyasa."

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 **APEX YAYINDA!** Yapay zeka tahmin motoru ve 5 parite aktif kanka.")

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
            msg += f"⚠️ {s} verisi alınamadı.\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_cuzdan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balance = exchange.fetch_balance()
        usdt_free = balance['total'].get('USDT', 0.0)
        await update.message.reply_text(f"💼 **OKX CÜZDAN BAKİYESİ**\n\nUSDT: `{usdt_free:.4f}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Cüzdan hatası: {e}")

async def cmd_set_rsi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BUY_RSI_THRESHOLD
    try:
        val = float(context.args[0])
        BUY_RSI_THRESHOLD = val
        await update.message.reply_text(f"✅ Alım RSI eşiği `{BUY_RSI_THRESHOLD}` oldu kanka!")
    except:
        await update.message.reply_text("⚠️ Örnek kullanım: `/set_rsi 28`", parse_mode="Markdown")

def main():
    # Render HTTP sunucusunu arka planda başlat
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("analiz", cmd_analiz))
    app.add_handler(CommandHandler("cuzdan", cmd_cuzdan))
    app.add_handler(CommandHandler("set_rsi", cmd_set_rsi))

    print("APEX Bot Başlatıldı...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
