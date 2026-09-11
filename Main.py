import os
import threading
import time
import json
import urllib.request
import hmac
import hashlib
import base64
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "apex_pro_super_secret_key_260526")

PIN_CODE = "260526"
TELEGRAM_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
CHAT_ID = "8982017587"

OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

AUTO_TRADE_ENABLED = True

# --- HAREKETLİ VE ESNETİLMİŞ RSI / SCALP AYARLARI ---
# RSI eşiğini daha esnek hale getirdik ki bot hemen tetiklensin kanka!
TARGET_RSI_THRESHOLD = 52.0  # Eskiden çok daha düşüktü, şimdi daha kolay yakalayacak
STOP_LOSS_PCT = 0.025
TAKE_PROFIT_PCT = 0.035
TRAILING_TRIGGER = 0.02
TRAILING_STOP = 0.01

crypto_cache = {
    "bitcoin": {"inst_id": "BTC-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:BTCUSDT"},
    "ethereum": {"inst_id": "ETH-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:ETHUSDT"},
    "solana": {"inst_id": "SOL-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:SOLUSDT"},
    "avalanche": {"inst_id": "AVAX-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:AVAXUSDT"},
    "chainlink": {"inst_id": "LINK-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:LINKUSDT"},
    "near": {"inst_id": "NEAR-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0, "tv_symbol": "BINANCE:NEARUSDT"},
    "dolar": {"price": "0.00"},
    "gram_altin": {"price": "0.00"},
    "ceyrek_altin": {"price": "0.00"}
}

last_alert_prices = {k: 0.0 for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]}
last_trade_state = {k: "NEUTRAL" for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]}
partial_tp_done = {k: False for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]}
buy_prices = {k: 0.0 for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]}
max_prices_during_trade = {k: 0.0 for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]}
daily_stats = {"total_trades": 0, "successful_trades": 0, "total_profit_pct": 0.0}
custom_target_alerts = {}
last_report_time = time.time()
REPORT_INTERVAL = 900


def send_telegram(message, chat_id=CHAT_ID, disable_notification=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "disable_notification": disable_notification
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
        {"command": "start", "description": "🤖 Botu Başlat ve Menüyü Gör"},
        {"command": "analiz", "description": "📈 Akıllı Çoklu Gösterge Piyasası"},
        {"command": "cuzdan", "description": "💼 OKX TR Cüzdan Bakiyesini Gör"},
        {"command": "rapor", "description": "📊 Performans Özeti"},
        {"command": "alarm", "description": "🔔 Fiyat Alarmı Kur"},
        {"command": "alarmlar", "description": "📋 Kurulu Aktif Alarmlar"},
        {"command": "alarmsil", "description": "🗑️ Alarm Sil"},
        {"command": "stop", "description": "🛑 Oto Motoru Durdur"},
        {"command": "baslat", "description": "▶️ Oto Motoru Çalıştır"},
        {"command": "btc", "description": "🪙 Bitcoin Anlık"},
        {"command": "eth", "description": "🪙 Ethereum Anlık"},
        {"command": "sol", "description": "🪙 Solana Anlık"},
        {"command": "dolar", "description": "💵 USD/TL Kuru"},
        {"command": "gram", "description": "🥇 Gram Altın"},
        {"command": "ceyrek", "description": "🥇 Çeyrek Altın"},
        {"command": "test", "description": "🧪 Bağlantı Testi"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Komut menüsü hatası: {e}")


def get_usdt_balance_num():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return 0.0
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
                for coin in details:
                    if coin.get("ccy") == "USDT":
                        return float(coin.get("availBal", "0"))
    except Exception as e:
        print(f"Bakiye okuma hatası: {e}")
    return 0.0


def execute_okx_order(inst_id, side, sz="1", sz_type="base_ccy"):
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return False, "API anahtarları eksik."
    request_path = "/api/v5/trade/order"
    method = "POST"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    body = {
        "instId": inst_id,
        "tdMode": "cash",
        "side": side,
        "ordType": "market",
        "sz": str(sz)
    }
    if side == "buy" and sz_type == "quote_ccy":
        body["tgtCcy"] = "quote_ccy"
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


def calculate_rsi_and_bb(closes, period=14):
    if len(closes) < period + 1:
        return 50.0, 0.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    rsi = 100.0 if avg_loss == 0 else round(100 - (100 / (1 + (avg_gain / avg_loss))), 1)
    
    slice_closes = closes[-20:] if len(closes) >= 20 else closes
    sma = sum(slice_closes) / len(slice_closes)
    variance = sum([((x - sma) ** 2) for x in slice_closes]) / len(slice_closes)
    std_dev = variance ** 0.5
    bb_lower = sma - (2 * std_dev)
    return rsi, bb_lower


def fetch_okx_ticker_and_indicators(inst_id):
    price, rsi_value, bb_lower = 0.0, 50.0, 0.0
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
                rsi_value, bb_lower = calculate_rsi_and_bb(closes)
    except Exception as e:
        print(f"OKX Veri hatası ({inst_id}): {e}")
    return price, rsi_value, bb_lower


def fetch_live_data():
    global crypto_cache
    coins = [k for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]]
    for coin in coins:
        p, rsi, bb_l = fetch_okx_ticker_and_indicators(crypto_cache[coin]["inst_id"])
        if p > 0:
            crypto_cache[coin]["price_num"] = p
            crypto_cache[coin]["price"] = f"{p:,.2f}"
            crypto_cache[coin]["rsi"] = rsi
            crypto_cache[coin]["bb_lower"] = bb_l
            
    try:
        usdt_p, _, _ = fetch_okx_ticker_and_indicators("USDT-TRY")
        if usdt_p > 0:
            crypto_cache["dolar"]["price"] = f"{usdt_p:.2f}"
            
        url_gold = "https://api.gold-api.com/price/XAU"
        req_gold = urllib.request.Request(url_gold, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_gold, timeout=5) as resp_gold:
            res_g = json.loads(resp_gold.read().decode())
            price_ons = float(res_g.get("price", 0))
            if price_ons > 0:
                gram = (price_ons / 31.1034768) * usdt_p
                crypto_cache["gram_altin"]["price"] = f"{gram:,.2f}"
                crypto_cache["ceyrek_altin"]["price"] = f"{(gram * 1.635):,.2f}"
    except Exception as e:
        print(f"Borsa Kur Hatası: {e}")


def check_auto_trade_signals():
    global last_trade_state, buy_prices, max_prices_during_trade, daily_stats, partial_tp_done
    if not AUTO_TRADE_ENABLED:
        return
    
    coins = [k for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]]
    for coin in coins:
        rsi = crypto_cache[coin]["rsi"]
        curr_p = crypto_cache[coin]["price_num"]
        bb_l = crypto_cache[coin]["bb_lower"]
        inst_id = crypto_cache[coin]["inst_id"]
        
        # ESNETİLMİŞ KOŞUL: RSI eşiğini yukarı çektik, artık çok daha rahat tetiklenecek!
        is_active_signal = (rsi <= TARGET_RSI_THRESHOLD) or (bb_l > 0 and curr_p <= bb_l * 1.005)
        
        if is_active_signal and last_trade_state[coin] != "BOUGHT":
            avail_usdt = get_usdt_balance_num()
            trade_amount = round(min(avail_usdt, 50.0), 2)
            if trade_amount >= 5.0:
                success, msg = execute_okx_order(inst_id, "buy", sz=trade_amount, sz_type="quote_ccy")
                if success:
                    last_trade_state[coin] = "BOUGHT"
                    partial_tp_done[coin] = False
                    buy_prices[coin] = curr_p
                    max_prices_during_trade[coin] = curr_p
                    send_telegram(
                        f"🚨 *[İŞLEM BİLDİRİMİ: ALIM YAPILDI (ESNEK MOD)]*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 **Coin:** `{coin.upper()}`\n"
                        f"💵 **Alış Fiyatı:** `{curr_p:,.2f}` $\n"
                        f"💰 **Kullanılan Tutar:** `{trade_amount}` USDT\n"
                        f"📊 **Sinyal (RSI):** `{rsi}` (Esnek Eşik Yakalandı)\n"
                        f"━━━━━━━━━━━━━━━━━━━",
                        disable_notification=False
                    )
        elif last_trade_state[coin] == "BOUGHT" and buy_prices[coin] > 0:
            entry_p = buy_prices[coin]
            pnl_pct = (curr_p - entry_p) / entry_p
            if curr_p > max_prices_during_trade[coin]:
                max_prices_during_trade[coin] = curr_p
            max_p = max_prices_during_trade[coin]
            drop_from_peak = (max_p - curr_p) / max_p
            
            if pnl_pct <= -STOP_LOSS_PCT:
                execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🛑 *[İŞLEM BİLDİRİMİ: STOP-LOSS]*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 **Coin:** `{coin.upper()}`\n"
                    f"📉 **Net Sonuç:** `%{pnl_pct*100:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━",
                    disable_notification=False
                )
            elif pnl_pct >= TAKE_PROFIT_PCT and not partial_tp_done[coin]:
                execute_okx_order(inst_id, "sell", sz="50%", sz_type="base_ccy")
                partial_tp_done[coin] = True
                send_telegram(
                    f"🎯 *[İŞLEM BİLDİRİMİ: KADEMELİ KÂR AL]*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 **Coin:** `{coin.upper()}`\n"
                    f"🚀 **Kilitlenen Kâr:** `+%{pnl_pct*100:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━",
                    disable_notification=False
                )
            elif (max_p - entry_p) / entry_p >= TRAILING_TRIGGER and drop_from_peak >= TRAILING_STOP:
                execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                if pnl_pct > 0:
                    daily_stats["successful_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🏆 *[İŞLEM BİLDİRİMİ: ZİRVE SATIŞI]*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 **Coin:** `{coin.upper()}`\n"
                    f"💰 **Toplam Kâr:** `+%{pnl_pct*100:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━",
                    disable_notification=False
                )


def background_worker():
    set_telegram_commands()
    while True:
        try:
            fetch_live_data()
            check_auto_trade_signals()
        except Exception as e:
            print(f"Arka plan worker hatası: {e}")
        time.sleep(20)


@app.route("/", methods=["GET", "POST"])
def index():
    if "authenticated" not in session:
        if request.method == "POST":
            if request.form.get("pin") == PIN_CODE:
                session["authenticated"] = True
                return redirect(url_for("index"))
            return render_template_string(LOGIN_TEMPLATE, error="Geçersiz PIN Kodu!")
        return render_template_string(LOGIN_TEMPLATE, error=None)
    
    return render_template_string(DASHBOARD_TEMPLATE, cache=crypto_cache)


LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Apex Bot Giriş</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #161b22; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); text-align: center; border: 1px solid #30363d; width: 300px; }
        input { width: 100%; padding: 10px; margin: 15px 0; background: #0d1117; border: 1px solid #30363d; color: white; border-radius: 6px; box-sizing: border-box; text-align: center; font-size: 18px; }
        button { background: #238636; color: white; border: none; padding: 10px 20px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; }
        button:hover { background: #2ea043; }
        .error { color: #f85149; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ APEX PRO GİRİŞ</h2>
        <form method="POST">
            <input type="password" name="pin" placeholder="PIN Kodu" required autofocus>
            <button type="submit">Giriş Yap</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Apex Pro Dashboard</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
        .badge { background: #238636; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }
        .card { background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
        .price { font-size: 24px; font-weight: bold; color: #58a6ff; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚡ APEX PRO TERMINAL</h2>
            <div class="badge">Aktif (Esnek Mod)</div>
        </div>
        <div class="grid">
            {% for k, v in cache.items() %}
            <div class="card">
                <h3>{{ k.upper() }}</h3>
                <div class="price">{{ v.price }} $</div>
                {% if v.rsi is defined %}
                <p style="margin-top: 10px; font-size: 13px; color: #8b949e;">RSI: {{ v.rsi }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
