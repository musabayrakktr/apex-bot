import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"

def send_telegram(message, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Telegram hatası: {e}")
        return False

@app.route('/')
def home():
    return "APEX Bot 7/24 Aktif ve İnteraktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/btc", "btc"]:
                price, support, res = get_binance_data('BTCUSDT')
                reply = f"🪙 *Bitcoin (BTC) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                price, support, res = get_binance_data('ETHUSDT')
                reply = f"🪙 *Ethereum (ETH) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                price, support, res = get_binance_data('SOLUSDT')
                reply = f"🪙 *Solana (SOL) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/start", "/test"]:
                send_telegram("🚀 *APEX Bot'a Hoş Geldin!*\n\nKomutlar:\n👉 /btc - Bitcoin bilgisi\n👉 /eth - Ethereum bilgisi\n👉 /sol - Solana bilgisi", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Telegram webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

def get_binance_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=30"
        res = requests.get(url, timeout=5).json()
        closes = [float(x[4]) for x in res]
        current_price = f"{closes[-1]:,.2f}"
        support = f"{min(closes[-20:]):,.2f}"
        resistance = f"{max(closes[-20:]):,.2f}"
        return current_price, support, resistance
    except Exception as e:
        print(f"Binance API hatası: {e}")
        return "Veri alınamadı", "Veri alınamadı", "Veri alınamadı"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
