import os
import time
from flask import Flask, request, jsonify
import threading
import ccxt
import requests

# Flask Web Sunucusu
app = Flask(__name__)

# Telegram Ayarları
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "SENIN_TELEGRAM_TOKENIN")
CHAT_ID = os.environ.get("CHAT_ID", "SENIN_CHAT_IDN")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

@app.route('/')
def home():
    return "APEX Bot 7/24 Aktif!"

# TradingView Webhook Alıcısı
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json or request.data.decode('utf-8')
        if isinstance(data, dict):
            msg_text = data.get("message", str(data))
        else:
            msg_text = str(data)
            
        send_telegram(f"🚨 *TRADINGVIEW SİNYALİ GELDi!*\n-----------------------------------\n{msg_text}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Sepetimizdeki Coinler (Arka plan taraması)
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
last_states = {symbol: None for symbol in SYMBOLS}

def format_price(val):
    return f"{val:,.2f}"

def analyze_market():
    exchange = ccxt.binance()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=50)
            closes = [x[4] for x in ohlcv]
            current_price = closes[-1]
            
            support = min(closes[-20:])
            resistance = max(closes[-20:])
            
            if current_price <= support * 1.002:
                state = "BUY"
            elif current_price >= resistance * 0.998:
                state = "SELL"
            else:
                state = "NEUTRAL"
            
            if state != last_states[symbol] or state in ["BUY", "SELL"]:
                last_states[symbol] = state
                
                if state == "BUY":
                    status_header = "🚨 *ALIM SİNYALİ (BUY)*"
                    status_desc = "🟢 *Fiyat destekte! Tepki alımı gelebilir.*"
                elif state == "SELL":
                    status_header = "⚠️ *SATIM SİNYALİ (SELL)*"
                    status_desc = "🔴 *Fiyat dirençte! Düzeltme riski var.*"
                else:
                    status_header = "📊 *PİYASA DURUM RAPORU*"
                    status_desc = "⚪ *Fiyat yatay bantta süzülüyor.*"

                coin_name = symbol.split('/')[0]

                msg = (
                    f"=======================\n"
                    f"⚡ *APEX TRADING BOT* | `{coin_name}`\n"
                    f"=======================\n\n"
                    f"{status_header}\n\n"
                    f"💵 *Güncel Fiyat:* `{format_price(current_price)} USDT`\n"
                    f"🛡 *Destek:* `{format_price(support)} USDT`\n"
                    f"🎯 *Direnç:* `{format_price(resistance)} USDT`\n\n"
                    f"📍 *Analiz:* {status_desc}\n"
                    f"-----------------------------------\n"
                    f"⏳ *Zaman Dilimi:* 15 Dakikalık"
                )
                
                send_telegram(msg)
        except Exception as e:
            print(f"{symbol} hatası: {e}")

def bot_loop():
    while True:
        analyze_market()
        time.sleep(900)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot_loop()
