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

AUTO_TRADE_ENABLED = True  # Otomatik Al-Sat Modu Aktif

crypto_cache = {
    "bitcoin": {"inst_id": "BTC-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0},
    "ethereum": {"inst_id": "ETH-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0},
    "solana": {"inst_id": "SOL-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0},
    "dolar": {"price": "0.00"},
    "gram_altin": {"price": "0.00"},
    "ceyrek_altin": {"price": "0.00"}
}

last_alert_prices = {"bitcoin": 0.0, "ethereum": 0.0, "solana": 0.0}
last_trade_state = {"bitcoin": "NEUTRAL", "ethereum": "NEUTRAL", "solana": "NEUTRAL"}

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

def execute_okx_order(inst_id, side, sz="10"):
    """OKX Üzerinden Otomatik Market Al/Sat Emri Gönderir"""
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return False, "API anahtarları eksik."

    request_path = "/api/v5/trade/order"
    method = "POST"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    body = {
        "instId": inst_id,
        "tdMode": "cash",
        "side": side,  # buy veya sell
        "ordType": "market",
        "sz": sz  # USDT tutarı veya coin adedi
    }
    body_json = json.dumps(body)
    message = timestamp + method + request_path + body_json
    
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
    req = urllib.request.Request(url, data=body_json.encode('utf-8'), headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0":
                return True, res["data"][0].get("ordId", "Başarılı")
            else:
                return False, res.get("msg", "Bilinmeyen hata")
    except Exception as e:
        return False, str(e)

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
            
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def fetch_okx_ticker_and_rsi(inst_id):
    price, rsi_value = 0.0, 50.0
    try:
        url_ticker = f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}"
        req_t = urllib.request.Request(url_ticker, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_t, timeout=5) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                price = float(res["data"][0]["last"])

        url_candles = f"https://www.okx.com/api/v5/market/candles?instId={inst_id}&bar=15m&limit=30"
        req_c = urllib.request.Request(url_candles, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_c, timeout=5) as response:
            res_c = json.loads(response.read().decode())
            if res_c.get("code") == "0" and res_c.get("data"):
                closes = [float(item[4]) for item in res_c["data"]]
                closes.reverse()
                rsi_value = calculate_rsi(closes)
    except Exception as e:
        print(f"OKX Veri hatası ({inst_id}): {e}")
    return price, rsi_value

def fetch_live_data():
    global crypto_cache
    for coin in ["bitcoin", "ethereum", "solana"]:
        p, rsi = fetch_okx_ticker_and_rsi(crypto_cache[coin]["inst_id"])
        if p > 0:
            crypto_cache[coin]["price_num"] = p
            crypto_cache[coin]["price"] = f"{p:,.2f}"
            crypto_cache[coin]["rsi"] = rsi

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

def check_auto_trade_signals():
    """RSI Dip/Tepe Durumlarına Göre Otomatik Borsa Emri Verir"""
    global last_trade_state
    if not AUTO_TRADE_ENABLED:
        return

    for coin in ["bitcoin", "ethereum", "solana"]:
        rsi = crypto_cache[coin]["rsi"]
        inst_id = crypto_cache[coin]["inst_id"]
        
        # OTO-ALIM SİNYALİ (RSI <= 30)
        if rsi <= 30 and last_trade_state[coin] != "BOUGHT":
            success, msg = execute_okx_order(inst_id, "buy", sz="10")  # 10 USDT'lik otomatik alım
            if success:
                last_trade_state[coin] = "BOUGHT"
                send_telegram(
                    f"🤖 *OTOMATİK ALIM GERÇEKLEŞTİ! ({coin.upper()})*\n\n"
                    f"🟢 **Sebep:** RSI Dibi ({rsi} <= 30)\n"
                    f"🪙 **Parite:** `{inst_id}`\n"
                    f"💳 **Emir Notu:** `{msg}`"
                )
            else:
                send_telegram(f"⚠️ *Otomatik Alım Başarısız ({coin.upper()}):* {msg}")

        # OTO-SATIŞ SİNYALİ (RSI >= 70)
        elif rsi >= 70 and last_trade_state[coin] == "BOUGHT":
            success, msg = execute_okx_order(inst_id, "sell", sz="10")
            if success:
                last_trade_state[coin] = "NEUTRAL"
                send_telegram(
                    f"🤖 *OTOMATİK SATIŞ GERÇEKLEŞTİ! ({coin.upper()})*\n\n"
                    f"🔴 **Sebep:** RSI Tepesi ({rsi} >= 70)\n"
                    f"🪙 **Parite:** `{inst_id}`\n"
                    f"💰 **Emir Notu:** Kâr kilitlendi. ({msg})"
                )

def background_scanner():
    global last_report_time
    while True:
        try:
            fetch_live_data()
            check_auto_trade_signals()  # Otomatik Emir Denetimi

            now = time.time()
            if now - last_report_time >= REPORT_INTERVAL:
                last_report_time = now
                report = generate_market_report()
                send_telegram(report)
        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        time.sleep(20)

# (Arayüz ve Webhook Bağlantıları Aynen Korunuyor)
