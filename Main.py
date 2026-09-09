import os
import threading
import time
import json
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"

# Fiyatları hafızada tutacağımız sözlük (Cache)
crypto_cache = {
    "bitcoin": "78,168.00",
    "ethereum": "2,450.00",
    "solana": "145.00"
}

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

# Arka planda sürekli fiyatları güncelleyen akıllı döngü (Render'ın takılmasını engeller)
def background_price_updater():
    global crypto_cache
    while True:
        try:
            url = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,solana"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode())
                for item in res['data']:
                    coin_id = item['id']
                    price_val = float(item['priceUsd'])
                    crypto_cache[coin_id] = f"{price_val:,.2f}"
                print("Fiyatlar başarıyla güncellendi:", crypto_cache)
        except Exception as e:
            print(f"Arka plan güncelleme hatası: {e}")
        
        # Her 60 saniyede bir fiyatları tazele
        time.sleep(60)

@app.route('/')
def home():
    return "APEX Bot 7/24 Aktif ve Bellek Modu Devrede!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/btc", "btc"]:
                price = crypto_cache.get("bitcoin", "Veri alınamadı")
                reply = f"🪙 *Bitcoin (BTC) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                price = crypto_cache.get("ethereum", "Veri alınamadı")
                reply = f"🪙 *Ethereum (ETH) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                price = crypto_cache.get("solana", "Veri alınamadı")
                reply = f"🪙 *Solana (SOL) Anlık Fiyat*\n\n💵 Fiyat: `{price}` $"
                send_telegram(reply, chat_id)
            elif text in ["/start", "/test", "/help"]:
                send_telegram("🚀 *APEX Bot Bellek Modunda Aktif!* \n\nKomutlar:\n👉 /btc - Bitcoin fiyatı\n👉 /eth - Ethereum fiyatı\n👉 /sol - Solana fiyatı", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Telegram webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    # Arka plan fiyat güncelleyicisini bağımsız bir iş parçacığı (thread) olarak başlatıyoruz
    t = threading.Thread(target=background_price_updater, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
