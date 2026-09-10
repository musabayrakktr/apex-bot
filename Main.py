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

AUTO_TRADE_ENABLED = True

# Ticaret Stratejisi Ayarları
STOP_LOSS_PCT = 0.02    # %2 Zarar Kes
TAKE_PROFIT_PCT = 0.03  # %3 Kâr Al

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
buy_prices = {"bitcoin": 0.0, "ethereum": 0.0, "solana": 0.0}
last_signal_state = {"bitcoin": "⚪ BEKLE", "ethereum": "⚪ BEKLE", "solana": "⚪ BEKLE"}

# Günlük Kâr İstatistikleri
daily_stats = {"total_trades": 0, "successful_trades": 0, "total_profit_pct": 0.0}
last_daily_report_date = ""

last_error_notify_time = {"bitcoin": 0, "ethereum": 0, "solana": 0}
custom_target_alerts = {}

last_report_time = time.time()
REPORT_INTERVAL = 900  # 15 dakika

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
        {"command": "analiz", "description": "📈 Akıllı RSI & Oto-Trade Raporu"},
        {"command": "cuzdan", "description": "💼 OKX TR Cüzdan Bakiyesini Gör"},
        {"command": "rapor", "description": "📊 Günlük Performans Özeti"},
        {"command": "alarm", "description": "🔔 Fiyat Alarmı Kur (Örn: /alarm btc 80000)"},
        {"command": "alarmlar", "description": "📋 Kurulu Aktif Alarmları Gör"},
        {"command": "alarmsil", "description": "🗑️ Kurulu Alarmı Sil (Örn: /alarmsil btc)"},
        {"command": "stop", "description": "🛑 Otomatik Alım Motorunu Durdur"},
        {"command": "baslat", "description": "▶️ Otomatik Alım Motorunu Çalıştır"},
        {"command": "btc", "description": "🪙 Bitcoin Anlık Durum"},
        {"command": "eth", "description": "🪙 Ethereum Anlık Durum"},
        {"command": "sol", "description": "🪙 Solana Anlık Durum"},
        {"command": "dolar", "description": "💵 Canlı USD/TL Borsa Kuru"},
        {"command": "gram", "description": "🥇 Gram Altın Fiyatı"},
        {"command": "ceyrek", "description": "🥇 Çeyrek Altın Fiyatı"},
        {"command": "test", "description": "🧪 Sistem ve Bağlantı Testi"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Komut menüsü hatası: {e}")

def execute_okx_order(inst_id, side, sz="1"):
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
        "sz": sz
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
        usdt_p, _ = fetch_okx_ticker_and_rsi("USDT-TRY")
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

def calculate_precision_signal(rsi_val):
    if rsi_val <= 30:
        return "🟢 KESİN ALIM BÖLGESİ (Dip Tespiti)", "🟢 GÜÇLÜ AL"
    elif rsi_val <= 42:
        return "🟢 KADEMELİ ALIM UYGUN", "🟢 KADEMELİ AL"
    elif rsi_val >= 70:
        return "🔴 KESİN SATIŞ BÖLGESİ (Doygunluk)", "🔴 KÂR AL / SAT"
    elif rsi_val >= 58:
        return "🟡 KÂR REALİZASYONU YAKIN", "🟡 İZLE / SAT"
    else:
        return "⚪ NÖTR (Sermaye Koruma Modu)", "⚪ BEKLE"

def check_auto_trade_signals():
    global last_trade_state, buy_prices, last_error_notify_time, daily_stats
    if not AUTO_TRADE_ENABLED:
        return

    now = time.time()
    for coin in ["bitcoin", "ethereum", "solana"]:
        rsi = crypto_cache[coin]["rsi"]
        curr_p = crypto_cache[coin]["price_num"]
        inst_id = crypto_cache[coin]["inst_id"]
        
        # 1. RSI DIP ALIM
        if rsi <= 30 and last_trade_state[coin] != "BOUGHT":
            success, msg = execute_okx_order(inst_id, "buy", sz="1")
            if success:
                last_trade_state[coin] = "BOUGHT"
                buy_prices[coin] = curr_p
                send_telegram(
                    f"🚨 *MÜKEMMEL DİP YAKALANDI! ({coin.upper()})*\n\n"
                    f"🟢 **Sebep:** RSI Aşırı Satım ({rsi} <= 30)\n"
                    f"💵 **Alış Fiyatı:** `{curr_p:,.2f}` $\n"
                    f"🛡️ **Stop-Loss:** `%{STOP_LOSS_PCT*100:.0f}` | 🎯 **Take-Profit:** `%{TAKE_PROFIT_PCT*100:.0f}`",
                    disable_notification=False
                )
            else:
                if now - last_error_notify_time[coin] > 900:
                    last_error_notify_time[coin] = now
                    send_telegram(
                        f"⚠️ *Otomatik Alım Başarısız ({coin.upper()}):* `{msg}`\n\n"
                        f"💡 *Not:* Hesabınızda USDT bakiyesi olmayabilir. Durdurmak için /stop yazabilirsiniz."
                    )

        # Pozisyondaysak: Stop-Loss, Take-Profit veya RSI Tepe Kontrolü
        elif last_trade_state[coin] == "BOUGHT" and buy_prices[coin] > 0:
            entry_p = buy_prices[coin]
            pnl_pct = (curr_p - entry_p) / entry_p

            # 2. STOP-LOSS
            if pnl_pct <= -STOP_LOSS_PCT:
                success, msg = execute_okx_order(inst_id, "sell", sz="1")
                if success:
                    last_trade_state[coin] = "NEUTRAL"
                    daily_stats["total_trades"] += 1
                    daily_stats["total_profit_pct"] += pnl_pct
                    send_telegram(
                        f"🛑 *STOP-LOSS TETİKLENDİ ({coin.upper()})*\n\n"
                        f"📉 **Değişim:** `%{pnl_pct*100:.2f}`\n"
                        f"💵 **Satış Fiyatı:** `{curr_p:,.2f}` $\n"
                        f"🛡️ Sermaye koruması için pozisyon kapatıldı.",
                        disable_notification=False
                    )

            # 3. TAKE-PROFIT
            elif pnl_pct >= TAKE_PROFIT_PCT:
                success, msg = execute_okx_order(inst_id, "sell", sz="1")
                if success:
                    last_trade_state[coin] = "NEUTRAL"
                    daily_stats["total_trades"] += 1
                    daily_stats["successful_trades"] += 1
                    daily_stats["total_profit_pct"] += pnl_pct
                    send_telegram(
                        f"🎯 *TAKE-PROFIT HEDEFİ ULAŞILDI! ({coin.upper()})*\n\n"
                        f"🚀 **Kâr:** `+%{pnl_pct*100:.2f}`\n"
                        f"💵 **Satış Fiyatı:** `{curr_p:,.2f}` $\n"
                        f"💰 Kâr kilitlendi, tebrikler patron!",
                        disable_notification=False
                    )

            # 4. RSI TEPESİ (RSI >= 70)
            elif rsi >= 70:
                success, msg = execute_okx_order(inst_id, "sell", sz="1")
                if success:
                    last_trade_state[coin] = "NEUTRAL"
                    daily_stats["total_trades"] += 1
                    if pnl_pct > 0: daily_stats["successful_trades"] += 1
                    daily_stats["total_profit_pct"] += pnl_pct
                    send_telegram(
                        f"🤖 *RSI TEPESİ SATIŞI ({coin.upper()})*\n\n"
                        f"🔴 **Sebep:** RSI Tepesi ({rsi} >= 70)\n"
                        f"📊 **Sonuç:** `%{pnl_pct*100:.2f}`\n"
                        f"💰 Kâr kilitlendi.",
                        disable_notification=False
                    )

def check_daily_report_schedule():
    global last_daily_report_date, daily_stats
    today_str = datetime.now().strftime('%Y-%m-%d')
    current_hour = datetime.now().hour
    
    if current_hour == 0 and last_daily_report_date != today_str:
        last_daily_report_date = today_str
        report = (
            "📊 *APEX BOT GÜNLÜK PERFORMANS RAPORU*\n\n"
            f"🔄 **Toplam İşlem Sayısı:** `{daily_stats['total_trades']}`\n"
            f"✅ **Başarılı İşlemler:** `{daily_stats['successful_trades']}`\n"
            f"📈 **Toplam Oransal Kâr:** `%{daily_stats['total_profit_pct']*100:.2f}`\n\n"
            f"💡 *Sistem yarın için tetikte beklemeye devam ediyor!*"
        )
        send_telegram(report, disable_notification=False)
        daily_stats = {"total_trades": 0, "successful_trades": 0, "total_profit_pct": 0.0}

def check_signal_change_alerts():
    global last_signal_state
    for coin in ["bitcoin", "ethereum", "solana"]:
        rsi = crypto_cache[coin]["rsi"]
        curr_p = crypto_cache[coin]["price"]
        _, current_sig = calculate_precision_signal(rsi)
        previous_sig = last_signal_state[coin]

        if current_sig != previous_sig:
            last_signal_state[coin] = current_sig
            if current_sig in ["🟢 GÜÇLÜ AL", "🟢 KADEMELİ AL", "🔴 KÂR AL / SAT", "🟡 İZLE / SAT"]:
                send_telegram(
                    f"🚨 *SİNYAL DEĞİŞİKLİĞİ UYARISI! ({coin.upper()})*\n\n"
                    f"📡 **Eski Sinyal:** `{previous_sig}`\n"
                    f"🎯 **Yeni Sinyal:** *{current_sig}*\n"
                    f"📊 **Anlık Fiyat:** `{curr_p}` $\n"
                    f"📈 **Canlı RSI:** `{rsi}`",
                    disable_notification=False
                )

def check_custom_price_alerts():
    global custom_target_alerts
    for coin_id, targets in list(custom_target_alerts.items()):
        curr_p = crypto_cache[coin_id]["price_num"]
        if curr_p == 0.0: continue
        
        for target_p in list(targets):
            if curr_p >= target_p:
                send_telegram(
                    f"🎯 *HEDEF FİYAT ALARMI TETİKLENDİ! ({coin_id.upper()})*\n\n"
                    f"🚀 *Anlık Fiyat:* `{curr_p:,.2f}` $\n"
                    f"📌 *Kurulan Hedef:* `{target_p:,.2f}` $",
                    disable_notification=False
                )
                targets.remove(target_p)
                
        if not targets:
            del custom_target_alerts[coin_id]

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

            if change_pct >= 1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(
                    f"🚀 *SATIŞ / KÂR AL SİNYALİ! ({coin_id.upper()})*\n\n"
                    f"📈 *Fiyat Sıçraması:* `{curr_p:,.2f}` $\n"
                    f"⚡ *Değişim:* `+{change_pct:.2f}%`",
                    disable_notification=False
                )
            elif change_pct <= -1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(
                    f"🛡️ *SERMAYE KORUMA / DIP ALARMI! ({coin_id.upper()})*\n\n"
                    f"📉 *Fiyat Düşüşü:* `{curr_p:,.2f}` $\n"
                    f"⚡ *Değişim:* `{change_pct:.2f}%`",
                    disable_notification=False
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
    
    status_text = "🟢 *Sistem Aktif - Otomatik Emir Motoru*" if AUTO_TRADE_ENABLED else "🔴 *Sistem DURDURULDU (Manuel Mod)*"

    return (
        "📡 *APEX OTO-TRADE & MİKRO-TİCARET RAPORU*\n\n"
        f"{status_text}\n\n"
        "📊 *Anlık Fiyatlar & RSI:*\n"
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
            check_auto_trade_signals()
            check_instant_movement()
            check_signal_change_alerts()
            check_custom_price_alerts()
            check_daily_report_schedule()

            now = time.time()
            if now - last_report_time >= REPORT_INTERVAL:
                last_report_time = now
                report = generate_market_report()
                send_telegram(report, disable_notification=True)
        except Exception as e:
            print(f"Tarama hatası: {e}")
        
        time.sleep(20)

@app.route('/')
def home():
    return "APEX Trade Motoru Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    global last_report_time, custom_target_alerts, AUTO_TRADE_ENABLED
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            raw_text = data["message"].get("text", "").strip()
            text = raw_text.lower()

            fetch_live_data()

            if text in ["/start", "start", "/help"]:
                set_telegram_commands()
                start_msg = (
                    "🤖 *APEX OTO-TRADING BOT DEVREDE!*\n\n"
                    "Hoş geldin patron! Sistem canlı RSI, otomatik borsa emri ve anlık sinyal değişikliklerini yönetir.\n\n"
                    "📌 *Tüm Komutlar Menü Butonuna Eklenmiştir!*"
                )
                send_telegram(start_msg, chat_id)

            elif text in ["/stop", "stop"]:
                AUTO_TRADE_ENABLED = False
                send_telegram("🛑 *OTOMATİK EMİR MOTORU DURDURULDU!*", chat_id)

            elif text in ["/baslat", "baslat"]:
                AUTO_TRADE_ENABLED = True
                send_telegram("▶️ *OTOMATİK EMİR MOTORU BAŞLATILDI!*", chat_id)

            elif text in ["/rapor", "rapor"]:
                report = (
                    "📊 *APEX BOT GÜNLÜK PERFORMANS RAPORU*\n\n"
                    f"🔄 **Toplam İşlem Sayısı:** `{daily_stats['total_trades']}`\n"
                    f"✅ **Başarılı İşlemler:** `{daily_stats['successful_trades']}`\n"
                    f"📈 **Toplam Oransal Kâr:** `%{daily_stats['total_profit_pct']*100:.2f}`"
                )
                send_telegram(report, chat_id)

            elif text.startswith("/alarm "):
                parts = raw_text.split()
                if len(parts) == 3:
                    coin_key = parts[1].lower()
                    if coin_key in ["btc", "bitcoin"]: coin_key = "bitcoin"
                    elif coin_key in ["eth", "ethereum"]: coin_key = "ethereum"
                    elif coin_key in ["sol", "solana"]: coin_key = "solana"
                    
                    try:
                        target_price = float(parts[2])
                        if coin_key in crypto_cache:
                            if coin_key not in custom_target_alerts:
                                custom_target_alerts[coin_key] = []
                            custom_target_alerts[coin_key].append(target_price)
                            send_telegram(f"✅ *Özel Hedef Alarmı Kuruldu! ({coin_key.upper()} - {target_price:,.2f} $)*", chat_id)
                        else:
                            send_telegram("⚠️ Sadece BTC, ETH ve SOL için alarm kurabilirsiniz.", chat_id)
                    except ValueError:
                        send_telegram("⚠️ Geçersiz fiyat formatı. Örn: `/alarm btc 80000`", chat_id)
                else:
                    send_telegram("⚠️ /alarm komutuna dokunup yanına coin ve hedef fiyat yazın. Örn: `/alarm btc 80000`", chat_id)

            elif text in ["/alarmlar", "alarmlar"]:
                if not custom_target_alerts:
                    send_telegram("🔔 *Kurulu aktif bir hedef fiyat alarmınız yok.*", chat_id)
                else:
                    msg = "🔔 *AKTİF HEDEF FİYAT ALARMLARI*\n\n"
                    for c_id, t_list in custom_target_alerts.items():
                        msg += f"🪙 *{c_id.upper()}*: {', '.join([f'`{p:,.2f} $`' for p in t_list])}\n"
                    send_telegram(msg, chat_id)

            elif text.startswith("/alarmsil"):
                parts = raw_text.split()
                if len(parts) == 2:
                    coin_key = parts[1].lower()
                    if coin_key in ["btc", "bitcoin"]: coin_key = "bitcoin"
                    elif coin_key in ["eth", "ethereum"]: coin_key = "ethereum"
                    elif coin_key in ["sol", "solana"]: coin_key = "solana"
                    
                    if coin_key in custom_target_alerts:
                        del custom_target_alerts[coin_key]
                        send_telegram(f"🗑️ *{coin_key.upper()} alarmları temizlendi.*", chat_id)
                    else:
                        send_telegram(f"⚠️ *{coin_key.upper()}* için kurulu alarm bulunamadı.", chat_id)
                else:
                    send_telegram("⚠️ /alarmsil komutuna dokunup yanına coin adını yazın. Örn: `/alarmsil btc`", chat_id)

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
                send_telegram(f"💵 *Canlı Dolar (OKX USDT/TRY)*: `{crypto_cache['dolar']['price']}` TL", chat_id)
            elif text in ["/gram", "gram"]:
                send_telegram(f"🥇 *Gram Altın*: `{crypto_cache['gram_altin']['price']}` TL", chat_id)
            elif text in ["/ceyrek", "çeyrek"]:
                send_telegram(f"🥇 *Çeyrek Altın*: `{crypto_cache['ceyrek_altin']['price']}` TL", chat_id)
            elif text in ["/test", "test"]:
                last_report_time = time.time()
                send_telegram("✅ *Tüm Komutlar Telegram Menüsüne Entegre Edildi!*", chat_id)
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
