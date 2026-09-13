import os
import time
import threading
import json
import urllib.request
from flask import Flask
from market import get_live_market_data
from strategy import analyze_market_for_dip

TELEGRAM_TOKEN = "8851186730:AAEChJwI1Uj7J0xfed-fZ4pEiyzVfyFZhcA"
app = Flask(__name__)

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

@app.route('/')
def home():
    return "Apex Bot 7/24 Aktif ve Çalışıyor! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    from flask import request
    try:
        data = request.get_json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()

            if text in ["/start", "/baslat"]:
                send_telegram(chat_id, "🚀 *APEX BOT AKTİF VE DEVREDE!*\nSol menüden dilediğin komutu seçebilirsin kanka!")
            elif text == "/cuzdan":
                send_telegram(chat_id, "💼 *APEX VIRTUAL CÜZDAN*\n💵 Bakiye: `$1,250.00`\n🪙 Varlık: `₺42,850.50`")
            elif text == "/analiz":
                veriler = get_live_market_data()
                cevap = "📊 *CANLI PİYASA ANALİZİ*\n"
                for item in veriler[:3]:
                    cevap += f"🪙 {item.get('parite', 'SOL/USDT')} - Fiyat: {item.get('fiyat', '100')}\n"
                send_telegram(chat_id, cevap)
            elif text == "/rapor":
                send_telegram(chat_id, "📋 *SİSTEM RAPORU*\n🟢 Render Sunucusu uyanık ve çalışıyor.")
    except Exception as e:
        print(f"Webhook işleme hatası: {e}")
    return {"status": "ok"}, 200

def trading_loop():
    print("🚀 Otonom Al-Sat Döngüsü Başlatıldı.")
    symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
    while True:
        try:
            for symbol in symbols:
                analyze_market_for_dip(symbol)
        except Exception as e:
            print(f"Döngü hatası: {e}")
        time.sleep(30)

if __name__ == "__main__":
    print("🌟 Apex Bot Kararlı Modda Başlatılıyor...")

    t_trade = threading.Thread(target=trading_loop)
    t_trade.daemon = True
    t_trade.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
