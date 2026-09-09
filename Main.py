import os
import time
from flask import Flask, request, jsonify
import threading
import ccxt
import requests

app = Flask(__name__)

# TELEGRAM BİLGİLERİ (DOĞRUDAN TANIMLI)
TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Yanıtı: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"Telegram hatası: {e}")
        return False

@app.route('/')
def home():
    return "APEX Bot 7/24 Aktif!"

@app.route('/test')
def test_msg():
    success = send_telegram("🧪 *APEX | TEST BİLDİRİMİ*\n\nSistem kusursuz çalışıyor kanka! 🚀")
    if success:
        return "Test mesajı Telegram'a başarıyla gönderildi!"
    else:
        return "Mesaj gönderilemedi! Token veya Chat ID hatalı."

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'POST':
            data = request.json or request.data.decode('utf-8')
            msg_text = data.get("message", str(data)) if isinstance(data, dict) else str(data)
        else:
            msg_text = "TradingView Test Bağlantısı Başarılı!"

        send_telegram(f"🚨 *TRADINGVIEW SİNYALİ*\n-----------------------------------\n{msg_text}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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
    send_telegram("🚀 *APEX BOT AKTİF!*\n-----------------------------------\nSepet: BTC, ETH, SOL taranıyor...")
    while True:
        analyze_market()
        time.sleep(900)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot_loop()
