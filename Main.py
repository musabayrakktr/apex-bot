import os
import threading
import time
import json
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"

# Hafıza (Cache): Fiyat, destek, direnç ve analiz durumu
crypto_cache = {
    "bitcoin": {"price": "78,168.00", "support": "77,952.20", "res": "79,401.00", "status": "Nötr. Fiyat aralıkta süzülüyor."},
    "ethereum": {"price": "2,450.00", "support": "2,400.00", "res": "2,520.00", "status": "Nötr."},
    "solana": {"price": "145.00", "support": "140.00", "res": "150.00", "status": "Nötr."}
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

# Arka planda hem fiyatları hem de destek/direnç seviyelerini güncelleyen akıllı döngü
def background_scanner():
    global crypto_cache
    # Bot ilk açıldığında test bildirimi atalım
    send_telegram("🟢 *APEX | Bağlantı Yenilendi. Sürekli Taraması ve Bellek Modu Aktif...*")
    
    while True:
        try:
            # CoinCap Markets API üzerinden anlık verileri çekiyoruz
            url = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,solana"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode())
                for item in res['data']:
                    coin_id = item['id']
                    p = float(item['priceUsd'])
                    # Basit ve stabil destek/direnç simülasyonu (Fiyatın %1 altı ve üstü)
                    sup = p * 0.99
                    res_val = p * 1.01
                    
                    crypto_cache[coin_id] = {
                        "price": f"{p:,.2f}",
                        "support": f"{sup:,.2f}",
                        "res": f"{res_val:,.2f}",
                        "status": "🎯 Fiyat takip ediliyor, alım/satım koşulları izleniyor."
                    }
        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        # Her 60 saniyede bir güncelle
        time.sleep(60)

@app.route('/')
def home():
    return "APEX Bot Tam Donanımlı 7/24 Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/btc", "btc"]:
                d = crypto_cache.get("bitcoin", {})
                reply = f"🪙 *Bitcoin (BTC) Anlık Durum*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $\n⏳ Durum: {d.get('status')}"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                d = crypto_cache.get("ethereum", {})
                reply = f"🪙 *Ethereum (ETH) Anlık Durum*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $\n⏳ Durum: {d.get('status')}"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                d = crypto_cache.get("solana", {})
                reply = f"🪙 *Solana (SOL) Anlık Durum*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $\n⏳ Durum: {d.get('status')}"
                send_telegram(reply, chat_id)
            elif text in ["/start", "/test", "/help"]:
                send_telegram("🚀 *APEX BOT AKTİF!*\n\nSepet: BTC, ETH, SOL taranıyor...\n\nKomutlar:\n👉 /btc - Bitcoin Durumu\n👉 /eth - Ethereum Durumu\n👉 /sol - Solana Durumu", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Telegram webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
