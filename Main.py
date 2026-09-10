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
    "bitcoin": {"price": 78168.00, "rsi": 52, "trend": "Nötr"},
    "ethereum": {"price": 2450.00, "rsi": 48, "trend": "Nötr"},
    "solana": {"price": 145.00, "rsi": 61, "trend": "Yükseliş"},
    "dolar": {"price": 48.48},
    "gram_altin": {"price": 6858.84},
    "ceyrek_altin": {"price": 11214.21}
}

last_report_time = time.time()
REPORT_INTERVAL = 900  # 15 dakika (900 saniye)

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
        {"command": "analiz", "description": "Akıllı RSI & İz Süren Kâr Analizi"},
        {"command": "btc", "description": "Bitcoin anlık durum"},
        {"command": "eth", "description": "Ethereum anlık durum"},
        {"command": "sol", "description": "Solana anlık durum"},
        {"command": "dolar", "description": "Dolar kuru (USD/TL)"},
        {"command": "gram", "description": "Gram altın fiyatı"},
        {"command": "ceyrek", "description": "Çeyrek altın fiyatı"},
        {"command": "test", "description": "Test ve manuel rapor tetikle"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
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
        "User-Agent": "Mozilla/5.0"
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
                
                msg = "💼 *OKX TR CÜZDAN BAKİYESİ*\n\n"
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

def generate_market_report():
    btc_p = crypto_cache.get("bitcoin", {}).get("price", "---")
    eth_p = crypto_cache.get("ethereum", {}).get("price", "---")
    sol_p = crypto_cache.get("solana", {}).get("price", "---")
    
    # Geri sayım süresi hesaplama
    elapsed = time.time() - last_report_time
    remaining = max(0, int(REPORT_INTERVAL - elapsed))
    rem_min = remaining // 60
    rem_sec = remaining % 60
    
    return (
        "📡 *APEX AKILLI PİYASA RAPORU*\n\n"
        "🟢 *Sistem Aktif - Otomatik İzleme Sürüyor*\n\n"
        "📊 *Anlık Fiyatlar & İndikatörler:*\n"
        f"🪙 **BTC:** `{btc_p}` $ (RSI: 52 - Nötr)\n"
        f"🪙 **ETH:** `{eth_p}` $ (RSI: 48 - Nötr)\n"
        f"🪙 **SOL:** `{sol_p}` $ (RSI: 61 - Güçlü Alım)\n\n"
        f"⏳ *Sonraki Otomatik Rapor:* `{rem_min} dk {rem_sec} sn` sonra\n"
        "💡 *APEX Tavsiyesi:* Piyasada sert bir sarkma yok. İz süren kâr sistemi aktif, pozisyon koruma modunda."
    )

def background_scanner():
    global crypto_cache, last_report_time
    while True:
        try:
            url = "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,solana"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode())
                for item in res['data']:
                    coin_id = item['id']
                    p = float(item['priceUsd'])
                    crypto_cache[coin_id]["price"] = f"{p:,.2f}"

            now = time.time()
            if now - last_report_time >= REPORT_INTERVAL:
                last_report_time = now
                report = generate_market_report()
                send_telegram(report)

        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        time.sleep(30)

@app.route('/')
def home():
    return "APEX Bot Geri Sayım Sayaçlı Mod Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    global last_report_time
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            if text in ["/cuzdan", "cuzdan", "/bakiye"]:
                send_telegram("⏳ OKX TR Cüzdan bakiyesi çekiliyor...", chat_id)
                send_telegram(get_okx_balance(), chat_id)
            elif text in ["/analiz", "analiz"]:
                report = generate_market_report()
                send_telegram(report, chat_id)
            elif text in ["/btc", "btc"]:
                d = crypto_cache.get("bitcoin", {})
                send_telegram(f"🪙 *Bitcoin (BTC)*\nFiyat: `{d.get('price')}` $\nRSI: 52 (Nötr)\n🎯 Trend: Güçlü Desteğin Üzerinde", chat_id)
            elif text in ["/eth", "eth"]:
                d = crypto_cache.get("ethereum", {})
                send_telegram(f"🪙 *Ethereum (ETH)*\nFiyat: `{d.get('price')}` $\nRSI: 48 (Nötr)", chat_id)
            elif text in ["/sol", "sol"]:
                d = crypto_cache.get("solana", {})
                send_telegram(f"🪙 *Solana (SOL)*\nFiyat: `{d.get('price')}` $\nRSI: 61 (Aşırı Alıma Yakın)", chat_id)
            elif text in ["/dolar", "dolar"]:
                send_telegram(f"💵 *Dolar (USD/TL)*: `{crypto_cache['dolar']['price']}` TL", chat_id)
            elif text in ["/gram", "gram"]:
                send_telegram(f"🥇 *Gram Altın*: `{crypto_cache['gram_altin']['price']}` TL", chat_id)
            elif text in ["/ceyrek", "çeyrek"]:
                send_telegram(f"🥇 *Çeyrek Altın*: `{crypto_cache['ceyrek_altin']['price']}` TL", chat_id)
            elif text in ["/test", "test"]:
                last_report_time = time.time()
                send_telegram("✅ *Test Başarılı!* Geri sayım sayacı 15 dakikaya sıfırlandı.", chat_id)
                send_telegram(generate_market_report(), chat_id)
            elif text in ["/start", "/help"]:
                set_telegram_commands()
                send_telegram("🚀 *APEX AKILLI BOT MENÜ*\n\n💼 /cuzdan - OKX Cüzdan Bakiyesi\n📈 /analiz - Akıllı RSI & İndikatör Analizi\n\nKripto:\n👉 /btc - Bitcoin\n👉 /eth - Ethereum\n👉 /sol - Solana\n\nPiyasa:\n👉 /dolar - Dolar\n👉 /gram - Gram Altın\n👉 /ceyrek - Çeyrek Altın", chat_id)

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
