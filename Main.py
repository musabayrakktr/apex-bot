import os
import threading
import time
import json
import urllib.request
import hmac
import hashlib
import base64
from datetime import datetime, timezone
from flask import Flask

app = Flask(__name__)

TELEGRAM_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
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
    "bitcoin": {"inst_id": "BTC-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
    "ethereum": {"inst_id": "ETH-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
    "solana": {"inst_id": "SOL-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
    "avalanche": {"inst_id": "AVAX-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
    "chainlink": {"inst_id": "LINK-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
    "near": {"inst_id": "NEAR-USDT", "price_num": 0.0, "price": "0.00", "rsi": 50.0, "bb_lower": 0.0},
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
        "OK-ACCESS-KEY": OKX_API_KEY, "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp, "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
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
    body = {"instId": inst_id, "tdMode": "cash", "side": side, "ordType": "market", "sz": str(sz)}
    if side == "buy" and sz_type == "quote_ccy":
        body["tgtCcy"] = "quote_ccy"
    body_json = json.dumps(body)
    message = timestamp + method + request_path + body_json
    mac = hmac.new(OKX_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode('utf-8')
    headers = {
        "OK-ACCESS-KEY": OKX_API_KEY, "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp, "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
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
    if len(closes) < period + 1: return 50.0, 0.0
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

def calculate_precision_signal(rsi_val, curr_price, bb_lower):
    if rsi_val <= 32 and (bb_lower > 0 and curr_price <= bb_lower * 1.005):
        return "🟢 ÇOKLU GÖSTERGE DİBİ"
    elif rsi_val <= 38: return "🟢 KADEMELİ ALIM UYGUN"
    elif rsi_val >= 70: return "🔴 KESİN SATIŞ BÖLGESİ"
    elif rsi_val >= 58: return "🟡 KÂR REALİZASYONU YAKIN"
    else: return "⚪ NÖTR (Sermaye Koruma)"

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

        is_strong_dip = (rsi <= 33) or (rsi <= 38 and bb_l > 0 and curr_p <= bb_l * 1.002)

        if is_strong_dip and last_trade_state[coin] != "BOUGHT":
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
                        f"🚨 *[İŞLEM BİLDİRİMİ: ALIM YAPILDI]*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🪙 **Coin:** `{coin.upper()}`\n"
                        f"💵 **Alış Fiyatı:** `{curr_p:,.2f}` $\n"
                        f"💰 **Kullanılan Tutar:** `{trade_amount}` USDT\n"
                        f"📊 **Sinyal:** RSI `{rsi}` + Bollinger Desteği\n"
                        f"🛡️ **Stop-Loss:** `%{STOP_LOSS_PCT*100:.1f}` | 🎯 **Hedef Kâr:** `%{TAKE_PROFIT_PCT*100:.1f}`\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"⚡ *Pozisyon Otomatik Takibe Alındı!*",
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
                    f"💵 **Satış Fiyatı:** `{curr_p:,.2f}` $\n"
                    f"📉 **Net Sonuç:** `%{pnl_pct*100:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🛡️ *Sermaye Koruma Modu Çalıştırıldı.*",
                    disable_notification=False
                )

            elif pnl_pct >= TAKE_PROFIT_PCT and not partial_tp_done[coin]:
                execute_okx_order(inst_id, "sell", sz="50%", sz_type="base_ccy")
                partial_tp_done[coin] = True
                send_telegram(
                    f"🎯 *[İŞLEM BİLDİRİMİ: KADEMELİ KÂR AL]*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 **Coin:** `{coin.upper()}`\n"
                    f"🚀 **Kilitlenen Kâr:** `+%{pnl_pct*100:.2f}` (%50 Satış)\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🛡️ *Kalan %50 Pozisyon İzleyen Stop Moduna Geçirildi!*",
                    disable_notification=False
                )

            elif (max_p - entry_p) / entry_p >= TRAILING_TRIGGER and drop_from_peak >= TRAILING_STOP:
                execute_okx_order(inst_id, "sell", sz="100%", sz_type="base_ccy")
                last_trade_state[coin] = "NEUTRAL"
                daily_stats["total_trades"] += 1
                if pnl_pct > 0: daily_stats["successful_trades"] += 1
                daily_stats["total_profit_pct"] += pnl_pct
                send_telegram(
                    f"🏆 *[İŞLEM BİLDİRİMİ: ZİRVE SATIŞI]*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 **Coin:** `{coin.upper()}`\n"
                    f"💰 **Toplam Kâr:** `+%{pnl_pct*100:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *İzleyen Stop Zirveden Satış Yaptı!*",
                    disable_notification=False
                )

def check_instant_movement():
    global last_alert_prices
    coins = [k for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]]
    for coin_id in coins:
        curr_p = crypto_cache[coin_id]["price_num"]
        prev_p = last_alert_prices[coin_id]
        if prev_p == 0.0:
            last_alert_prices[coin_id] = curr_p
            continue
        if curr_p > 0 and prev_p > 0:
            change_pct = ((curr_p - prev_p) / prev_p) * 100
            if change_pct >= 1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(f"🚀 *SATIŞ / KÂR AL SİNYALİ! ({coin_id.upper()})*\n\n📈 *Fiyat Sıçraması:* `{curr_p:,.2f}` $\n⚡ *Değişim:* `+{change_pct:.2f}%`", disable_notification=False)
            elif change_pct <= -1.5:
                last_alert_prices[coin_id] = curr_p
                send_telegram(f"🛡️ *SERMAYE KORUMA / DIP ALARMI! ({coin_id.upper()})*\n\n📉 *Fiyat Düşüşü:* `{curr_p:,.2f}` $\n⚡ *Değişim:* `{change_pct:.2f}%`", disable_notification=False)

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

def get_okx_balance():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return "⚠️ OKX API anahtarları eksik! Render ayarlarını kontrol edin."
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
    url = f"https://www.okx.com{request_path}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                details = res["data"][0].get("details", [])
                if not details: return "💼 *OKX Cüzdanınızda kullanılabilir bakiye bulunamadı.*"
                msg = "💼 *OKX TR CÜZDAN BAKİYESİ*\n\n"
                for coin in details:
                    if float(coin.get("eq", "0")) > 0:
                        msg += f"🪙 *{coin.get('ccy')}*: `{float(coin.get('eq', '0')):.4f}`\n"
                return msg
            else:
                return f"❌ OKX Hatası: {res.get('msg', 'Bilinmeyen hata')}"
    except Exception as e:
        return f"❌ OKX Bağlantı Hatası: {e}"

def generate_analiz_report():
    fetch_live_data()
    msg = "📡 *APEX MULTI-HARVESTER CANLI ANALİZ*\n\n"
    coins = [k for k in crypto_cache if k not in ["dolar", "gram_altin", "ceyrek_altin"]]
    for coin in coins:
        p_str = crypto_cache[coin]['price']
        rsi_v = crypto_cache[coin]['rsi']
        bb_l = crypto_cache[coin]['bb_lower']
        p_num = crypto_cache[coin]['price_num']
        signal = calculate_precision_signal(rsi_v, p_num, bb_l)
        msg += f"🪙 **{coin.upper()[:3]}:** `{p_str}` $ | RSI: `{rsi_v}` -> *{signal}*\n"
    
    msg += f"\n💵 **USD/TL:** `{crypto_cache['dolar']['price']}` TL\n\n"
    
    # Dakika + Saniye Detaylı Geri Sayım
    elapsed = time.time() - last_report_time
    remaining_sec = max(0, int(REPORT_INTERVAL - elapsed))
    rem_min = remaining_sec // 60
    rem_sec = remaining_sec % 60
    
    msg += f"⏳ *Sonraki Otomatik Rapor:* `{rem_min} dk {rem_sec} sn` kaldı"
    return msg

def handle_message(raw_text, chat_id):
    global AUTO_TRADE_ENABLED, custom_target_alerts
    text = raw_text.lower()
    fetch_live_data()

    if text in ["/start", "start", "/help"]:
        set_telegram_commands()
        start_msg = (
            "🚀 *APEX MULTI-HARVESTER DEVREDE!*\n\n"
            "Hoş geldin patron! 5.000 TL Çoklu Altcoin Sepeti (BTC, ETH, SOL, AVAX, LINK, NEAR), RSI + Bollinger çoklu gösterge süzgeci ve kademeli kâr alma motoru aktif.\n\n"
            "📌 Menüden komutlara erişebilirsin."
        )
        send_telegram(start_msg, chat_id)

    elif text.startswith("/alarm "):
        parts = raw_text.split()
        if len(parts) == 3:
            coin_key = parts[1].lower()
            try:
                target_price = float(parts[2])
                if coin_key not in custom_target_alerts:
                    custom_target_alerts[coin_key] = []
                custom_target_alerts[coin_key].append(target_price)
                send_telegram(f"✅ *Hedef Alarmı Kuruldu! ({coin_key.upper()} - {target_price:,.2f} $)*", chat_id)
            except ValueError:
                send_telegram("⚠️ Geçersiz format. Örn: `/alarm btc 80000`", chat_id)

    elif text in ["/alarmlar", "alarmlar"]:
        if not custom_target_alerts:
            send_telegram("🔔 *Kurulu aktif hedef alarmınız yok.*", chat_id)
        else:
            msg = "🔔 *AKTİF HEDEF ALARMLARI*\n\n"
            for c_id, t_list in custom_target_alerts.items():
                msg += f"🪙 *{c_id.upper()}*: {', '.join([f'`{p:,.2f} $`' for p in t_list])}\n"
            send_telegram(msg, chat_id)

    elif text.startswith("/alarmsil"):
        parts = raw_text.split()
        if len(parts) == 2:
            coin_key = parts[1].lower()
            if coin_key in custom_target_alerts:
                del custom_target_alerts[coin_key]
                send_telegram(f"🗑️ *{coin_key.upper()} alarmları temizlendi.*", chat_id)

    elif text in ["/stop", "stop"]:
        AUTO_TRADE_ENABLED = False
        send_telegram("🛑 *OTOMATİK EMİR MOTORU DURDURULDU!*", chat_id)

    elif text in ["/baslat", "baslat"]:
        AUTO_TRADE_ENABLED = True
        send_telegram("▶️ *OTOMATİK EMİR MOTORU BAŞLATILDI!*", chat_id)

    elif text in ["/cuzdan", "cuzdan", "/bakiye"]:
        send_telegram("⏳ OKX TR Cüzdan bakiyesi çekiliyor...", chat_id)
        send_telegram(get_okx_balance(), chat_id)

    elif text in ["/analiz", "analiz"]:
        send_telegram(generate_analiz_report(), chat_id)

    elif text in ["/rapor", "rapor"]:
        rapor_msg = (
            "📊 *APEX PERFORMANS RAPORU*\n\n"
            f"🔄 **Toplam İşlem:** `{daily_stats['total_trades']}`\n"
            f"✅ **Başarılı İşlem:** `{daily_stats['successful_trades']}`\n"
            f"📈 **Toplam Oransal Kâr:** `%{daily_stats['total_profit_pct']*100:.2f}`\n\n"
            f"🤖 *Otomatik Motor:* {'🟢 Aktif' if AUTO_TRADE_ENABLED else '🔴 Durduruldu'}"
        )
        send_telegram(rapor_msg, chat_id)

    elif text in ["/dolar", "dolar"]:
        send_telegram(f"💵 *Dolar*: `{crypto_cache['dolar']['price']}` TL", chat_id)
    elif text in ["/gram", "gram"]:
        send_telegram(f"🥇 *Gram Altın*: `{crypto_cache['gram_altin']['price']}` TL", chat_id)
    elif text in ["/ceyrek", "çeyrek"]:
        send_telegram(f"🥇 *Çeyrek Altın*: `{crypto_cache['ceyrek_altin']['price']}` TL", chat_id)
    elif text in ["/test", "test"]:
        send_telegram("✅ *Multi-Harvester Sistem Tamamen Aktif!*", chat_id)

def telegram_polling_listener():
    offset = 0
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except Exception as e:
        print(f"Webhook silme hatası: {e}")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.loads(response.read().decode())
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            chat_id = update["message"]["chat"]["id"]
                            raw_text = update["message"].get("text", "").strip()
                            if raw_text:
                                handle_message(raw_text, chat_id)
        except Exception as e:
            time.sleep(3)

def background_scanner():
    global last_report_time
    while True:
        try:
            fetch_live_data()
            check_auto_trade_signals()
            check_instant_movement()
            check_custom_price_alerts()

            if time.time() - last_report_time >= REPORT_INTERVAL:
                last_report_time = time.time()
                # Sesli ve Kesin Bildirim ile Otomatik Rapor Gönderimi
                send_telegram(generate_analiz_report(), disable_notification=False)

        except Exception as e:
            print(f"Tarama hatası: {e}")
        time.sleep(20)

@app.route('/')
def home():
    return "APEX Multi-Harvester Aktif!"

if __name__ == '__main__':
    threading.Thread(target=background_scanner, daemon=True).start()
    threading.Thread(target=telegram_polling_listener, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
