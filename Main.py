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

STOP_LOSS_PCT = 0.025     
TAKE_PROFIT_PCT = 0.035   
TRAILING_TRIGGER = 0.02   
TRAILING_STOP = 0.01      

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
max_prices_during_trade = {"bitcoin": 0.0, "ethereum": 0.0, "solana": 0.0}
last_signal_state = {"bitcoin": "⚪ BEKLE", "ethereum": "⚪ BEKLE", "solana": "⚪ BEKLE"}

daily_stats = {"total_trades": 0, "successful_trades": 0, "total_profit_pct": 0.0}
last_daily_report_date = ""
last_error_notify_time = {"bitcoin": 0, "ethereum": 0, "solana": 0}
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
    global last_trade_state, buy_prices, max_prices_during_trade, last_error_notify_time, daily_stats
    if not AUTO_TRADE_ENABLED:
        return

    now = time.time()
    for coin in ["bitcoin", "ethereum", "solana"]:
        rsi = crypto_cache[coin]["rsi"]
        curr_p = crypto_cache[coin]["price_num"]
        inst_id = crypto_cache[coin]["inst_id"]
        
        if rsi <= 30 and last_trade_state[coin] != "BOUGHT":
            avail_usdt = get_usdt_balance_num()
            trade_amount = round(avail_usdt * 0.90, 2)
            
            if trade_amount >= 1.0:
                success, msg = execute_okx_order(inst_id, "buy", sz=trade_amount, sz_type="quote_ccy")
                if success:
                    last_trade_state[coin] = "BOUGHT"
                    buy_prices[coin] = curr_p
                    max_prices_during_trade[coin] = curr_p
                    send_telegram(
                        f"🚨 *MÜKEMMEL DİP YAKALANDI! ({coin.upper()})*\n\n"
                        f"🟢 **Sebep:** RSI Dibi ({rsi} <= 30)\n"
                        f"💵 **Alış Fiyatı:** `{curr_p:,.2f}` $\n"
                        f"💰 **Kullanılan Bütçe:** `{trade_amount}` USDT\n"
                        f"🛡️ **Stop-Loss:** `%{STOP_LOSS_PCT*100:.1f}` | 🎯 **Take-Profit:** `%{TAKE_PROFIT_PCT*100:.1f}`",
                        disable_notification=False
                    )
                else:
                    if now - last_error_notify_time[coin] > 900:
                        last_error_notify_time[coin] = now
                        send_telegram(f"⚠️ *Alım Başarısız ({coin.upper()}):* `{msg}`")

        elif last_trade_state[coin] == "BOUGHT" and buy_prices[coin] > 0:
            entry_p = buy_prices[coin]
            pnl_pct = (curr_p - entry_p) / entry_p
            
            if curr_p > max_prices_during_trade[coin]:
                max_prices_during_trade[coin] = curr_p
            
            max_p = max_prices_during_trade[coin]
            drop_from_peak = (max_p - curr_p) / max_p

            if pnl_pct <= -STOP_LOSS_PCT:
                success, msg = execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🛑 *STOP-LOSS TETİKLENDİ ({coin.upper()})*\n\n"
                    f"📉 **Net Sonuç:** `%{pnl_pct*100:.2f}`\n"
                    f"💵 **Satış Fiyatı:** `{curr_p:,.2f}` $",
                    disable_notification=False
                )

            elif pnl_pct >= TAKE_PROFIT_PCT:
                success, msg = execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                daily_stats["successful_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🎯 *TAKE-PROFIT KÂR KİLİTLENDİ! ({coin.upper()})*\n\n"
                    f"🚀 **Net Kâr:** `+%{pnl_pct*100:.2f}`\n"
                    f"💵 **Satış Fiyatı:** `{curr_p:,.2f}` $",
                    disable_notification=False
                )

            elif (max_p - entry_p) / entry_p >= TRAILING_TRIGGER and drop_from_peak >= TRAILING_STOP:
                success, msg = execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                if pnl_pct > 0: daily_stats["successful_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🛡️ *KÂR KORUMA SATIŞI (TRAILING STOP) ({coin.upper()})*\n\n"
                    f"📈 **Zirveden Düşüş:** `%{drop_from_peak*100:.2f}`\n"
                    f"💰 **Kilitlenen Kâr:** `+%{pnl_pct*100:.2f}`",
                    disable_notification=False
                )

            elif rsi >= 70:
                success, msg = execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                if pnl_pct > 0: daily_stats["successful_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🤖 *RSI TEPESİ SATIŞI ({coin.upper()})*\n\n"
                    f"🔴 **Sebep:** RSI Tepesi ({rsi} >= 70)",
                    disable_notification=False
                )

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
    
    status_text = "🟢 *Sistem Aktif - Otomatik Emir Motoru*" if AUTO_TRADE_ENABLED else "🔴 *Sistem DURDURULDU*"

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
        f"• SOL: {sol_status}"
    )

def process_message(raw_text, chat_id):
    global last_report_time, custom_target_alerts, AUTO_TRADE_ENABLED
    text = raw_text.lower()
    fetch_live_data()

    if text in ["/start", "start", "/help"]:
        set_telegram_commands()
        start_msg = (
            "🤖 *APEX OTO-TRADING BOT DEVREDE!*\n\n"
            "Hoş geldin patron! 200 TL mikro-bütçe koruma algoritmaları ve izleyen stop devrede.\n\n"
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
            send_telegram("⚠️ Kullanım örneği: `/alarm btc 80000`", chat_id)

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
            send_telegram("⚠️ Kullanım örneği: `/alarmsil btc`", chat_id)

    elif text in ["/cuzdan", "cuzdan", "/bakiye"]:
        send_telegram("⏳ OKX TR Cüzdan bakiyesi çekiliyor...", chat_id)
        
        # OKX Bakiye Metni
        if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
            bal_msg = "⚠️ OKX API anahtarları eksik!"
        else:
            try:
                request_path = "/api/v5/account/balance"
                timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                message = timestamp + "GET" + request_path
                mac = hmac.new(OKX_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
                sign = base64.b64encode(mac.digest()).decode('utf-8')
                headers = {
                    "OK-ACCESS-KEY": OKX_API_KEY, "OK-ACCESS-SIGN": sign,
                    "OK-ACCESS-TIMESTAMP": timestamp, "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
                    "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
                }
                req = urllib.request.Request(f"https://www.okx.com{request_path}", headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode())
                    if res.get("code") == "0" and res.get("data"):
                        details = res["data"][0].get("details", [])
                        bal_msg = "💼 *OKX TR CÜZDAN BAKİYESİ*\n\n"
                        for coin in details:
                            if float(coin.get("eq", "0")) > 0:
                                bal_msg += f"🪙 *{coin.get('ccy')}*: `{float(coin.get('eq', '0')):.4f}`\n"
                    else:
                        bal_msg = f"❌ OKX Hatası: {res.get('msg')}"
            except Exception as e:
                bal_msg = f"❌ Bağlantı Hatası: {e}"
        send_telegram(bal_msg, chat_id)

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
        send_telegram("✅ *200 TL Mikro-Bütçe Modu & İzleyen Stop Aktif!*", chat_id)
        send_telegram(generate_market_report(), chat_id)

# --- TELEGRAM LONG POLLING (WEBHOOK GEREKTİRMEZ, ANINDA ÇALIŞIR) ---
def telegram_polling_listener():
    set_telegram_commands()
    offset = 0
    print("Telegram Polling Dinleyicisi Aktifleşti...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode())
                if data.get("ok"):
                    for result in data.get("result", []):
                        offset = result["update_id"] + 1
                        message = result.get("message", {})
                        raw_text = message.get("text", "").strip()
                        chat_id = message.get("chat", {}).get("id")
                        if raw_text and chat_id:
                            process_message(raw_text, chat_id)
        except Exception as e:
            print(f"Polling döngü hatası: {e}")
            time.sleep(3)

def background_scanner():
    while True:
        try:
            fetch_live_data()
            check_auto_trade_signals()
        except Exception as e:
            print(f"Tarama hatası: {e}")
        time.sleep(20)

@app.route('/')
def home():
    return "APEX Trade Motoru ve Polling Aktif!"

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            raw_text = data["message"].get("text", "").strip()
            if raw_text:
                process_message(raw_text, chat_id)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    # Webhook kurma derdi yok, Polling arka planda mesajları anında yakalayacak!
    threading.Thread(target=telegram_polling_listener, daemon=True).start()
    threading.Thread(target=background_scanner, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
