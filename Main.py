import os
from flask import Flask, request, jsonify
import urllib.request
import json

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
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
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
                price = get_crypto_price('bitcoin')
                reply = f"🪙 *Bitcoin (BTC) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                price = get_crypto_price('ethereum')
                reply = f"🪙 *Ethereum (ETH) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                price = get_crypto_price('solana')
                reply = f"🪙 *Solana (SOL) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/start", "/test", "/help"]:
                send_telegram("🚀 *APEX Bot'a Hoş Geldin!*\n\nKomutlar:\n👉 /btc - Bitcoin fiyatı\n👉 /eth - Ethereum fiyatı\n👉 /sol - Solana fiyatı", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Telegram webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

def get_crypto_price(coin_id):
    try:
        # CoinCap API: Asla IP engeline takılmaz, dünyadaki en stabil açık API'lerden biridir
        url = f"https://api.coincap.io/v2/assets/{coin_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            price_val = float(res['data']['priceUsd'])
            return f"{price_val:,.2f}"
    except Exception as e:
        print(f"Fiyat çekme hatası: {e}")
        return "Veri alınamadı"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
