import os
import time
from flask import Flask, request, jsonify
import threading
import ccxt
import requests

app = Flask(__name__)

# TELEGRAM BİLGİLERİ
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

@app.route('/test')
def test_msg():
    success = send_telegram("🧪 *APEX | TEST BİLDİRİMİ*\n\nİnteraktif sistem kusursuz çalışıyor kanka! 🚀")
    if success:
        return "Test mesajı Telegram'a başarıyla gönderildi!"
    else:
        return "Mesaj gönderilemedi!"

# TELEGRAM'DAN GELEN KOMUTLARI YÖNETEN ENDPOINT (WEBHOOK)
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/btc", "btc"]:
                price, support, res = get_coin_data('BTC/USDT')
                reply = f"🪙 *Bitcoin (BTC) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                price, support, res = get_coin_data('ETH/USDT')
                reply = f"🪙 *Ethereum (ETH) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                price, support, res = get_coin_data('SOL/USDT')
                reply = f"🪙 *Solana (SOL) Anlık Durum*\n\n💵 Fiyat: `{price}`\n🛡 Destek: `{support}`\n🎯 Direnç: `{res}`"
                send_telegram(reply, chat_id)
            elif text in ["/start", "/test"]:
                send_telegram("🚀 *APEX Bot'a Hoş Geldin!*\n\nKomutlar:\n👉 /btc - Bitcoin bilgisi\n👉 /eth - Ethereum bilgisi\n👉 /sol - Solana bilgisi", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Telegram webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

def get_coin_data(symbol):
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=30)
        closes = [x[4] for x in ohlcv]
        current_price = f"{closes[-1]:,.2f}"
        support = f"{min(closes[-20:]):,.2f}"
        resistance = f"{max(closes[-20:]):,.2f}"
        return current_price, support, resistance
    except:
        return "Veri alınamadı", "Veri alınamadı", "Veri alınamadı"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    # Otomatik arka plan döngüsü istersen buraya eklenebilir
