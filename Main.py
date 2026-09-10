import os
import threading
import time
import json
import urllib.request
import hmac
import hashlib
import base64
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"

# OKX API Bilgileri
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

crypto_cache = {
    "bitcoin": {"price": 78168.00, "support": 77952.20, "res": 79401.00},
    "ethereum": {"price": 2450.00, "support": 2400.00, "res": 2520.00},
    "solana": {"price": 145.00, "support": 140.00, "res": 150.00},
    "dolar": {"price": 48.48},
    "gram_altin": {"price": 6858.84},
    "ceyrek_altin": {"price": 11214.21}
}

last_alerts = {"bitcoin": "", "ethereum": "", "solana": ""}

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

def set_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Botu başlat ve menüyü gör"},
        {"command": "cuzdan", "description": "OKX TR Cüzdan Bakiyesini Gör"},
        {"command": "btc", "description": "Bitcoin anlık durum ve analiz"},
        {"command": "eth", "description": "Ethereum anlık durum ve analiz"},
        {"command": "sol", "description": "Solana anlık durum ve analiz"},
        {"command": "dolar", "description": "Dolar kuru (USD/TL)"},
        {"command": "gram", "description": "Gram altın fiyatı"},
        {"command": "ceyrek", "description": "Çeyrek altın fiyatı"},
        {"command": "test", "description": "Test bildirimi gönder"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
        print("Telegram menü komutları güncellendi.")
    except Exception as e:
        print(f"Komut menüsü hatası: {e}")

def get_okx_balance():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return "⚠️ OKX API anahtarları eksik! Render ayarlarını kontrol edin."

    request_path = "/api/v5/account/balance"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    message = timestamp + "GET" + request_path
    
    mac = hmac.new(OKX_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode('utf-8')

    headers = {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    url = f"https://www.okx.com{request_path}"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                details = res["data"][0].get("details", [])
                if not details:
                    return "💼 *OKX Cüzdanınızda kullanılabilir bakiye bulunamadı.*"
                
                msg = "💼 *OKX CÜZDAN BAKİYESİ*\n\n"
                for coin in details:
                    ccy = coin.get("ccy")
                    bal = float(coin.get("eq", "0"))
                    avail = float(coin.get("availBal", "0"))
                    if bal > 0:
                        msg += f"🪙 *{ccy}*: `{bal:.4f}` (Kullanılabilir: `{avail:.4f}`)\n"
                return msg
            else:
                return f"❌ OKX Hatası: {res.get('msg', 'Bilinmeyen hata')}"
    except Exception as e:
        return f"❌ OKX Bağlantı Hatası: {e}"

def background_scanner():
    global crypto_cache, last_alerts
    scan_count = 0
    
    while True:
        try:
            url = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,solana"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode())
                for item in res['data']:
                    coin_id = item['id']
                    p = float(item['priceUsd'])
                    # Hassasiyeti biraz arttırarak dinamik destek/direnç koridoru
                    sup = p * 0.995
                    res_val = p * 1.005
                    
                    alert_msg = ""
                    # Daha hassas tetiklenme eşiği (%0.5 yaklaşma)
                    if p <= sup * 1.005:
                        alert_msg = f"🚨 *ALARM! AL FIRSATI / DESTEK SEVİYESİ*\n\n🪙 {coin_id.upper()} desteğe çok yakın!\n💵 Anlık Fiyat: `{p:,.2f}` $\n🛡 Destek: `{sup:,.2f}` $"
                    elif p >= res_val * 0.995:
                        alert_msg = f"⚠️ *DİKKAT! DİRENÇ / SATIŞ BÖLGESİ*\n\n🪙 {coin_id.upper()} direnç bölgesini zorluyor!\n💵 Anlık Fiyat: `{p:,.2f}` $\n🎯 Direnç: `{res_val:,.2f}` $"

                    # Farklı bir sinyal oluştuysa doğrudan Telegram'a bas
                    if alert_msg and last_alerts.get(coin_id) != alert_msg:
                        send_telegram(alert_msg)
                        last_alerts[coin_id] = alert_msg

                    crypto_cache[coin_id] = {
                        "price": f"{p:,.2f}",
                        "support": f"{sup:,.2f}",
                        "res": f"{res_val:,.2f}"
                    }

            # Her 30 dakikada bir (30 taramada bir) otomatik durum özet bildirimi at
            scan_count += 1
            if scan_count >= 30:
                btc_p = crypto_cache.get("bitcoin", {}).get("price", "---")
                eth_p = crypto_cache.get("ethereum", {}).get("price", "---")
                sol_p = crypto_cache.get("solana", {}).get("price", "---")
                summary = f"📊 *PERİYODİK PİYASA BİLDİRİMİ*\n\nBot aktif çalışıyor kanka. Anlık durumlar:\n🪙 BTC: `{btc_p}` $\n🪙 ETH: `{eth_p}` $\n🪙 SOL: `{sol_p}` $"
                send_telegram(summary)
                scan_count = 0

        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        time.sleep(60)

@app.route('/')
def home():
    return "APEX Bot OKX Entegrasyonlu Mod Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/cuzdan", "cuzdan", "/bakiye", "bakiye", "/cüzdan", "cüzdan"]:
                send_telegram("⏳ OKX TR Cüzdan bakiyesi çekiliyor...", chat_id)
                bal_msg = get_okx_balance()
                send_telegram(bal_msg, chat_id)
            elif text in ["/btc", "btc"]:
                d = crypto_cache.get("bitcoin", {})
                reply = f"🪙 *Bitcoin (BTC)*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $"
                send_telegram(reply, chat_id)
            elif text in ["/eth", "eth"]:
                d = crypto_cache.get("ethereum", {})
                reply = f"🪙 *Ethereum (ETH)*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $"
                send_telegram(reply, chat_id)
            elif text in ["/sol", "sol"]:
                d = crypto_cache.get("solana", {})
                reply = f"🪙 *Solana (SOL)*\n\n💵 Fiyat: `{d.get('price')}` $\n🛡 Destek: `{d.get('support')}` $\n🎯 Direnç: `{d.get('res')}` $"
                send_telegram(reply, chat_id)
            elif text in ["/dolar", "dolar"]:
                d = crypto_cache.get("dolar", {})
                reply = f"💵 *Dolar (USD/TL)*\n\nKur: `{d.get('price')}` TL"
                send_telegram(reply, chat_id)
            elif text in ["/gram", "gram"]:
                d = crypto_cache.get("gram_altin", {})
                reply = f"🥇 *Gram Altın*\n\nFiyat: `{d.get('price')}` TL"
                send_telegram(reply, chat_id)
            elif text in ["/ceyrek", "çeyrek"]:
                d = crypto_cache.get("ceyrek_altin", {})
                reply = f"🥇 *Çeyrek Altın*\n\nFiyat: `{d.get('price')}` TL"
                send_telegram(reply, chat_id)
            elif text in ["/test", "test"]:
                send_telegram("✅ *Test Başarılı!*\nAPEX Bot al-sat alarm tarayıcısı aktif.", chat_id)
            elif text in ["/start", "/help"]:
                set_telegram_commands()
                send_telegram("🚀 *APEX BOT MENÜ*\n\n💼 /cuzdan - OKX Cüzdan Bakiyesi\n\nKripto:\n👉 /btc - Bitcoin\n👉 /eth - Ethereum\n👉 /sol - Solana\n\nPiyasa:\n👉 /dolar - Dolar\n👉 /gram - Gram Altın\n👉 /ceyrek - Çeyrek Altın", chat_id)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook hatası: {e}")
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    set_telegram_commands()
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
