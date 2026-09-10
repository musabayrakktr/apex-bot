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

OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

crypto_cache = {
    "bitcoin": {"price_num": 0.0, "price": "0.00", "rsi": 50},
    "ethereum": {"price_num": 0.0, "price": "0.00", "rsi": 50},
    "solana": {"price_num": 0.0, "price": "0.00", "rsi": 50},
    "dolar": {"price": "0.00"},
    "gram_altin": {"price": "0.00"},
    "ceyrek_altin": {"price": "0.00"}
}

# Fiyat geçmişi kaydı (Ani hareket tespiti için)
last_alert_prices = {"bitcoin": 0.0, "ethereum": 0.0, "solana": 0.0}

last_report_time = time.time()
REPORT_INTERVAL = 900  # 15 dakika

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
        {"command": "analiz", "description": "Akıllı RSI & Sinyal Analizi"},
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

def fetch_okx_ticker(inst_id):
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                return float(res["data"][0]["last"])
    except Exception as e:
        print(f"OKX Ticker hatası ({inst_id}): {e}")
    return 0.0

def fetch_live_data():
    global crypto_cache
    btc = fetch_okx_ticker("BTC-USDT")
    eth = fetch_okx_ticker("ETH-USDT")
    sol = fetch_okx_ticker("SOL-USDT")

    if btc > 0:
        crypto_cache["bitcoin"]["price_num"] = btc
        crypto_cache["bitcoin"]["price"] = f"{btc:,.2f}"
    if eth > 0:
        crypto_cache["ethereum"]["price_num"] = eth
        crypto_cache["ethereum"]["price"] = f"{eth:,.2f}"
    if sol > 0:
        crypto_cache["solana"]["price_num"] = sol
        crypto_cache["solana"]["price"] = f"{sol:,.2f}"

    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            try_rate = res['rates'].get('TRY', 0)
            if try_rate > 0:
                crypto_cache["dolar"]["price"] = f"{try_rate:.2f}"
                
                gold_url = "https://api.gold-api.com/price/XAU"
                req_gold = urllib.request.Request(gold_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_gold, timeout=5) as resp_gold:
                    res_g = json.loads(resp_gold.read().decode())
                    price_ons = float(res_g.get("price", 0))
                    if price_ons > 0:
                        gram = (price_ons / 31.1034768) * try_rate
                        crypto_cache["gram_altin"]["price"] = f"{gram:,.2f}"
                        crypto_cache["ceyrek_altin"]["price"] = f"{(gram * 1.635):,.2f}"
    except Exception as e:
        print(f"Döviz/Altın hatası: {e}")

def calculate_precision_signal(rsi_val):
    if rsi_val <= 30:
        return "🟢 KESİN ALIM BÖLGESİ (Dip Tespiti)", "🟢 GÜÇLÜ AL"
    elif rsi_val <= 40:
        return "🟢 KADEMELİ ALIM UYGUN", "🟢 AL"
    elif rsi_val >= 70:
        return "🔴 KESİN SATIŞ BÖLGESİ (Doygunluk)", "🔴 KÂR AL / SAT"
    elif rsi_val >= 60:
        return "🟡 KÂR REALİZASYONU YAKIN", "🟡 İZLE / SAT"
    else:
        return "⚪ NÖTR (Sermaye Koruma Modu)", "⚪ POZİSYON KORU"

def check_instant_movement():
    global last_alert_prices
    for coin_id in ["bitcoin", "ethereum", "solana"]:
        curr_p = crypto_cache[coin_id]["price_num"]
        prev_p = last_alert_prices[coin_id]

        if prev_p == 0.0:
            last_alert_prices[coin_id] = curr_p
            continue

        if curr_p > 0 and prev_p > 0:
            change_pct = ((curr_p - prev_p) / prev_p) * 100

            # Hassas Risk Koruma Limitleri (%1.5 Ani Değişim)
            if change_pct >= 1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(
                    f"🚀 *SATIŞ / KÂR AL SİNYALİ! ({coin_id.upper()})*\n\n"
                    f"📈 *Fiyat Sıçraması:* `{curr_p:,.2f}` $\n"
                    f"⚡ *Değişim:* `+{change_pct:.2f}%`\n"
                    f"💡 *Öneri:* Kâr kilitleniyor, kademeli satış düşünülebilir."
                )
            elif change_pct <= -1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(
                    f"🛡️ *SERMAYE KORUMA / DIP ALARMI! ({coin_id.upper()})*\n\n"
                    f"📉 *Fiyat Düşüşü:* `{curr_p:,.2f}` $\n"
                    f"⚡ *Değişim:* `{change_pct:.2f}%`\n"
                    f"💡 *Öneri:* Stop-Loss koruması aktif. Dip alım fırsatı değerlendirilebilir."
                )

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
    fetch_live_data()
    btc_p = crypto_cache.get("bitcoin", {}).get("price", "---")
    eth_p = crypto_cache.get("ethereum", {}).get("price", "---")
    sol_p = crypto_cache.get("solana", {}).get("price", "---")
    usd_p = crypto_cache.get("dolar", {}).get("price", "---")
    
    btc_rsi = crypto_cache["bitcoin"]["rsi"]
    eth_rsi = crypto_cache["ethereum"]["rsi"]
    sol_rsi = crypto_cache["solana"]["rsi"]

    btc_status, btc_sig = calculate_precision_signal(btc_rsi)
    eth_status, eth_sig = calculate_precision_signal(eth_rsi)
    sol_status, sol_sig = calculate_precision_signal(sol_rsi)

    elapsed = time.time() - last_report_time
    remaining = max(0, int(REPORT_INTERVAL - elapsed))
    rem_min = remaining // 60
    rem_sec = remaining % 60
    
    return (
        "📡 *APEX AKILLI MİKRO-TİCARET RAPORU*\n\n"
        "🟢 *Sistem Aktif - Hassas Risk Yönetimi*\n\n"
        "📊 *Anlık Fiyatlar & Sinyaller:*\n"
        f"🪙 **BTC:** `{btc_p}` $ | RSI: `{btc_rsi}` -> *{btc_sig}*\n"
        f"🪙 **ETH:** `{eth_p}` $ | RSI: `{eth_rsi}` -> *{eth_sig}*\n"
        f"🪙 **SOL:** `{sol_p}` $ | RSI: `{sol_rsi}` -> *{sol_sig}*\n"
        f"💵 **USD/TL:** `{usd_p}` TL\n\n"
        "🎯 *STRATEJİK SERMAYE DURUMU:*\n"
        f"• BTC: {btc_status}\n"
        f"• ETH: {eth_status}\n"
        f"• SOL: {sol_status}\n\n"
        f"⏳ *Sonraki Otomatik Rapor:* `{rem_min} dk {rem_sec} sn` sonra"
    )

def background_scanner():
    global last_report_time
    while True:
        try:
            fetch_live_data()
            check_instant_movement()

            now = time.time()
            if now - last_report_time >= REPORT_INTERVAL:
                last_report_time = now
                report = generate_market_report()
                send_telegram(report)
        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        time.sleep(20)

@app.route('/')
def home():
    return "APEX Hassas Risk Yönetim Motoru Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    global last_report_time
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()

            fetch_live_data()

            if text in ["/start", "start", "/help"]:
                set_telegram_commands()
                start_msg = (
                    "🤖 *APEX TRADING & MONITORING BOT DEVREDE!*\n\n"
                    "Hoş geldin patron! Sistem hem 15 dakikada bir rutin rapor atar hem de sert fiyat hareketlerinde anında uyarır.\n\n"
                    "📌 *Hızlı Komutlar:*\n"
                    "💼 /cuzdan - OKX TR Cüzdan Bakiyesi\n"
                    "📈 /analiz - Akıllı RSI & Sinyal Analizi\n\n"
                    "🪙 *Kripto:*\n"
                    "👉 /btc | /eth | /sol\n\n"
                    "💵 *Piyasa:*\n"
                    "👉 /dolar | /gram | /ceyrek"
                )
                send_telegram(start_msg, chat_id)
            elif text in ["/cuzdan", "cuzdan", "/bakiye"]:
                send_telegram("⏳ OKX TR Cüzdan bakiyesi çekiliyor...", chat_id)
                send_telegram(get_okx_balance(), chat_id)
            elif text in ["/analiz", "analiz"]:
                send_telegram(generate_market_report(), chat_id)
            elif text in ["/btc", "btc"]:
                rsi = crypto_cache['bitcoin']['rsi']
                _, sig = calculate_precision_signal(rsi)
                send_telegram(f"🪙 *Bitcoin (BTC)*: `{crypto_cache['bitcoin']['price']}` $\nRSI: `{rsi}` | Sinyal: *{sig}*", chat_id)
            elif text in ["/eth", "eth"]:
                rsi = crypto_cache['ethereum']['rsi']
                _, sig = calculate_precision_signal(rsi)
                send_telegram(f"🪙 *Ethereum (ETH)*: `{crypto_cache['ethereum']['price']}` $\nRSI: `{rsi}` | Sinyal: *{sig}*", chat_id)
            elif text in ["/sol", "sol"]:
                rsi = crypto_cache['solana']['rsi']
                _, sig = calculate_precision_signal(rsi)
                send_telegram(f"🪙 *Solana (SOL)*: `{crypto_cache['solana']['price']}` $\nRSI: `{rsi}` | Sinyal: *{sig}*", chat_id)
            elif text in ["/dolar", "dolar"]:
                send_telegram(f"💵 *Canlı Dolar (USD/TL)*: `{crypto_cache['dolar']['price']}` TL", chat_id)
            elif text in ["/gram", "gram"]:
                send_telegram(f"🥇 *Gram Altın*: `{crypto_cache['gram_altin']['price']}` TL", chat_id)
            elif text in ["/ceyrek", "çeyrek"]:
                send_telegram(f"🥇 *Çeyrek Altın*: `{crypto_cache['ceyrek_altin']['price']}` TL", chat_id)
            elif text in ["/test", "test"]:
                last_report_time = time.time()
                send_telegram("✅ *Test Başarılı!* Hassas tarama motoru aktif edildi.", chat_id)
                send_telegram(generate_market_report(), chat_id)

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
