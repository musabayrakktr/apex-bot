import os
import time
from flask import Flask
import threading
import ccxt

# Flask Web Sunucusu (Render'ın kapanmaması için)
app = Flask(__name__)

@app.route('/')
def home():
    return "APEX Bot 7/24 Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Bot Ana Kodları
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SENIN_TELEGRAM_TOKENIN")
CHAT_ID = os.environ.get("CHAT_ID", "SENIN_CHAT_IDN")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

# Sepetimizdeki Coinler
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
last_states = {symbol: None for symbol in SYMBOLS}

def analyze_market():
    exchange = ccxt.binance()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=50)
            closes = [x[4] for x in ohlcv]
            current_price = closes[-1]
            
            # Basit Destek / Direnç Seviyeleri
            support = min(closes[-20:])
            resistance = max(closes[-20:])
            
            # Sinyal Durumu Belirleme
            if current_price <= support * 1.002:
                state = "BUY"
            elif current_price >= resistance * 0.998:
                state = "SELL"
            else:
                state = "NEUTRAL"
            
            # Sinyal değiştiğinde veya BUY/SELL durumunda bildirim at
            if state != last_states[symbol] or state in ["BUY", "SELL"]:
                last_states[symbol] = state
                
                emoji = "🟢" if state == "BUY" else "🔴" if state == "SELL" else "⏳"
                msg = (
                    f"🤖 *APEX | DURUM RAPORU*\n\n"
                    f"📌 *Varlık:* {symbol}\n"
                    f"💰 *Fiyat:* {current_price:.2f} $\n"
                    f"🛡 *Destek:* {support:.2f} $\n"
                    f"🎯 *Direnç:* {resistance:.2f} $\n\n"
                    f"{emoji} *Durum:* {state}"
                )
                send_telegram(msg)
                print(f"[{symbol}] Bildirim gönderildi: {state}")
            else:
                print(f"[{symbol}] Durum değişmedi ({state}), bildirim atılmadı.")
                
        except Exception as e:
            print(f"{symbol} taranırken hata oluştu: {e}")

def bot_loop():
    send_telegram("🚀 *APEX | Sepet Tarama Modu Aktif!* (BTC, ETH, SOL)")
    while True:
        analyze_market()
        time.sleep(900)  # 15 dakikada bir tarama yapar

if __name__ == '__main__':
    # Flask sunucusunu ayrı bir thred'de başlat
    threading.Thread(target=run_flask).start()
    # Bot döngüsünü başlat
    bot_loop()
