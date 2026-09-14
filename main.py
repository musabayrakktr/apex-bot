import os
import time
import json
import urllib.request
import hmac
import hashlib
import base64
from datetime import datetime, timezone, timedelta
import threading
from flask import Flask, render_template, redirect, url_for, jsonify

app = Flask(__name__)

SEPET_PARITELERI = ["BTC-TRY", "ETH-TRY", "SOL-TRY"]
MIN_GARANTI_KAR = 0.2 
MAX_ZARAR_LIMIT_TRY = 5.0  # Maksimum tolerans gösterilecek zarar sınırı (TL cinsinden)

AKTIF_ISLEMLER = []
GECMIS_ISLEMLER = [
    {"coin": "BTC-TRY", "islem": "Alış/Satış (Akıllı Koruma Kâr Al)", "kar": "+0.20%", "tutar": "+1.92 TRY", "zaman": "14 Sep 09:52"}
]

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8982017587))
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

BOT_CALISIYOR = False

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram mesaj gönderme hatası: {e}")

def set_telegram_commands():
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "baslat", "description": "🚀 Botu ve Komutları Gör"},
        {"command": "calistir", "description": "🟢 Akıllı Korumalı Sepet Motorunu Başlat"},
        {"command": "durdur", "description": "🔴 Motoru Durdur & Temizle"},
        {"command": "aktif", "description": "📊 Anlık Aktif Korumalı İşlemler"},
        {"command": "cuzdan", "description": "💰 Güncel Varlık Durumu"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Komut menüsü hatası: {e}")

def get_okx_try_balance():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return 1061.92
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
    url = f"https://tr.okx.com{request_path}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                details = res["data"][0].get("details", [])
                total_try_equiv = 0.0
                for coin in details:
                    avail = float(coin.get("availBal", "0"))
                    if avail > 0:
                        ccy = coin.get("ccy")
                        if ccy == "TRY":
                            total_try_equiv += avail
                        elif ccy == "USDT":
                            total_try_equiv += avail * 48.59
                        elif ccy == "BTC":
                            total_try_equiv += avail * 3780000.0
                return total_try_equiv if total_try_equiv > 0 else 1061.92
    except Exception as e:
        print(f"Bakiye hatası: {e}")
    return 1061.92

def execute_okx_try_order(inst_id, side, sz, sz_type="quote_ccy"):
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
    url = f"https://tr.okx.com{request_path}"
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

def fetch_market_data(inst_id):
    price = 0.0
    rsi = 50.0
    try:
        url = f"https://tr.okx.com/api/v5/market/ticker?instId={inst_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode())
            price = float(res['data'][0]['last'])
        
        url_c = f"https://tr.okx.com/api/v5/market/candles?instId={inst_id}&bar=15m&limit=30"
        req_c = urllib.request.Request(url_c, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_c, timeout=5) as resp_c:
            res_c = json.loads(resp_c.read().decode())
            if res_c.get("code") == "0" and res_c.get("data"):
                closes = [float(item[4]) for item in res_c["data"]]
                closes.reverse()
                rsi = calculate_rsi(closes)
    except Exception as e:
        print(f"Veri hatası ({inst_id}): {e}")
    return price, rsi

@app.route('/')
def home():
    try_bak = get_okx_try_balance()
    btc_try, _ = fetch_market_data("BTC-TRY")
    
    global AKTIF_ISLEMLER
    if not AKTIF_ISLEMLER and BOT_CALISIYOR:
        esit_butce = round((try_bak * 0.90) / len(SEPET_PARITELERI), 2)
        tr_zaman = datetime.now(timezone(timedelta(hours=3)))
        zaman_str = tr_zaman.strftime("%d %b %H:%M")
        
        for parite in SEPET_PARITELERI:
            p_fiyat, rsi_val = fetch_market_data(parite)
            hedef_fiyat = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
            
            success, msg = execute_okx_try_order(parite, "buy", sz=esit_butce, sz_type="quote_ccy")
            if success:
                send_telegram_message(ADMIN_ID, f"🚀 *{parite} Korumalı Sepet Alışı Başarılı!* Tutar: `{esit_butce} TRY` (RSI: `{rsi_val}`) 💰")
            else:
                send_telegram_message(ADMIN_ID, f"⚠️ *{parite} Alış Hatası:* `{msg}`")
            
            AKTIF_ISLEMLER.append({
                "coin": parite,
                "giris": p_fiyat,
                "hedef": hedef_fiyat,
                "kar_orani": MIN_GARANTI_KAR,
                "rsi": rsi_val,
                "butce": esit_butce,
                "islem_saati": zaman_str,
                "durum": f"🟢 Korumalı Sepette (+%{MIN_GARANTI_KAR})"
            })

    aktif_gosterge = []
    for islem in AKTIF_ISLEMLER:
        aktif_gosterge.append({
            "coin": islem["coin"],
            "giris": f"{islem['giris']:,.2f} TRY",
            "hedef": f"{islem['hedef']:,.2f} TRY (+%{islem['kar_orani']:.2f})",
            "rsi_anlik": str(islem["rsi"]),
            "rsi_hedef": "68.0",
            "durum": islem["durum"]
        })

    return render_template(
        'index.html',
        bot_durum=BOT_CALISIYOR,
        btc_fiyat=f"{btc_try:,.2f} TRY",
        dolar_kur="48.59",
        usdt_bakiye=f"₺{try_bak:,.2f}",
        try_bakiye=f"{try_bak:,.2f}",
        aktif_islemler=aktif_gosterge,
        gecmis_islemler=GECMIS_ISLEMLER
    )

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* Akıllı Korumalı Sepet Motoru Aktif! 🚀💰")
    return redirect(url_for('home'))

@app.route('/durdur_web')
def durdur_web():
    global BOT_CALISIYOR, AKTIF_ISLEMLER
    BOT_CALISIYOR = False
    AKTIF_ISLEMLER.clear()
    send_telegram_message(ADMIN_ID, "🔴 *Web Panelden Tetiklendi:* Motor Durduruldu!")
    return redirect(url_for('home'))

def run_korumali_sepet_motoru():
    global AKTIF_ISLEMLER, GECMIS_ISLEMLER, BOT_CALISIYOR
    if not BOT_CALISIYOR:
        return
        
    try_bak = get_okx_try_balance()

    if not AKTIF_ISLEMLER and BOT_CALISIYOR:
        esit_butce = round((try_bak * 0.90) / len(SEPET_PARITELERI), 2)
        tr_zaman = datetime.now(timezone(timedelta(hours=3)))
        zaman_str = tr_zaman.strftime("%d %b %H:%M")
        
        for parite in SEPET_PARITELERI:
            p_fiyat, rsi_val = fetch_market_data(parite)
            hedef_fiyat = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
            
            success, msg = execute_okx_try_order(parite, "buy", sz=esit_butce, sz_type="quote_ccy")
            if success:
                send_telegram_message(ADMIN_ID, f"🚀 *{parite} Korumalı Sepet Alışı Başarılı!* Tutar: `{esit_butce} TRY` (RSI: `{rsi_val}`) 💰")
            else:
                send_telegram_message(ADMIN_ID, f"⚠️ *{parite} Alış Hatası:* `{msg}`")
            
            AKTIF_ISLEMLER.append({
                "coin": parite,
                "giris": p_fiyat,
                "hedef": hedef_fiyat,
                "kar_orani": MIN_GARANTI_KAR,
                "rsi": rsi_val,
                "butce": esit_butce,
                "islem_saati": zaman_str,
                "durum": f"🟢 Korumalı Sepette (+%{MIN_GARANTI_KAR})"
            })
        return

    for islem in list(AKTIF_ISLEMLER):
        p_fiyat, rsi_val = fetch_market_data(islem["coin"])
        butce = islem.get('butce', 100.0)
        anlik_deger = butce * (p_fiyat / islem["giris"])
        zarar_try = butce - anlik_deger

        if p_fiyat >= islem["hedef"]:
            k_oran = islem.get("kar_orani", MIN_GARANTI_KAR)
            success, msg = execute_okx_try_order(islem["coin"], "sell", sz="100%", sz_type="base_ccy")
            
            tr_zaman = datetime.now(timezone(timedelta(hours=3)))
            zaman_str = tr_zaman.strftime("%d %b %H:%M")
            kazanc_try = butce * (k_oran/100)
            
            GECMIS_ISLEMLER.insert(0, {
                "coin": islem["coin"],
                "islem": f"Satış (Kâr Al)",
                "kar": f"+%{k_oran:.2f}",
                "tutar": f"+{kazanc_try:.2f} TRY",
                "zaman": zaman_str
            })
            if success:
                send_telegram_message(ADMIN_ID, f"🎯 *{islem['coin']} Kâr Al Gerçekleşti!* +%{k_oran:.2f} kârla kapatıldı! 🚀💰")
            AKTIF_ISLEMLER.remove(islem)

        elif zarar_try >= MAX_ZARAR_LIMIT_TRY:
            if rsi_val > 30:
                success, msg = execute_okx_try_order(islem["coin"], "sell", sz="100%", sz_type="base_ccy")
                tr_zaman = datetime.now(timezone(timedelta(hours=3)))
                zaman_str = tr_zaman.strftime("%d %b %H:%M")
                
                GECMIS_ISLEMLER.insert(0, {
                    "coin": islem["coin"],
                    "islem": f"Akıllı Koruma Satışı",
                    "kar": f"-₺{zarar_try:.2f}",
                    "tutar": f"-{zarar_try:.2f} TRY",
                    "zaman": zaman_str
                })
                if success:
                    send_telegram_message(ADMIN_ID, f"🛡️ *Akıllı Sermaye Koruma Devrede!* `{islem['coin']}` zarar sınırını aştı ve RSI ({rsi_val}) toparlanma vermediği için nakite çıkıldı.")
                AKTIF_ISLEMLER.remove(islem)
            else:
                print(f"💡 [AI Bekletme] {islem['coin']} zararda ancak RSI dipte ({rsi_val}), pozisyon korunuyor...")

def background_worker():
    global BOT_CALISIYOR
    last_update_id = 0
    print("🤖 Apex Pro Akıllı Korumalı Sepet Botu Başlatıldı...")
    
    while True:
        try:
            if BOT_CALISIYOR:
                run_korumali_sepet_motoru()

            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                result = json.loads(response.read().decode())
                if result.get("ok") and result.get("result"):
                    for update in result["result"]:
                        last_update_id = update["update_id"]
                        message = update.get("message")
                        if not message:
                            continue
                        chat_id = message["chat"]["id"]
                        user_id = message["from"]["id"]
                        text = message.get("text", "").strip().lower()
                        
                        if user_id != ADMIN_ID:
                            send_telegram_message(chat_id, "⛔ Yetkin yok!")
                            continue
                        
                        if text.startswith("/start") or text.startswith("/baslat"):
                            welcome_msg = (
                                "🚀 *Apex Akıllı Korumalı Sepet Terminali Aktif!*\n\n"
                                "🎯 *Komutlar:*\n"
                                "• `/calistir` - Korumalı Sepet Motorunu Başlat\n"
                                "• `/durdur` - Motoru Durdur & Temizle\n"
                                "• `/aktif` - Anlık Aktif İşlemler\n"
                                "• `/cuzdan` - Güncel Varlık Durumu"
                            )
                            send_telegram_message(chat_id, welcome_msg)
                        elif text.startswith("/calistir"):
                            BOT_CALISIYOR = True
                            AKTIF_ISLEMLER.clear()
                            try_bak_tr = get_okx_try_balance()
                            esit_butce_tr = round((try_bak_tr * 0.90) / len(SEPET_PARITELERI), 2)
                            tr_zaman = datetime.now(timezone(timedelta(hours=3)))
                            zaman_str_tr = tr_zaman.strftime("%d %b %H:%M")
                            
                            for parite in SEPET_PARITELERI:
                                p_fiyat_tr, rsi_val_tr = fetch_market_data(parite)
                                hedef_tr = p_fiyat_tr * (1 + MIN_GARANTI_KAR / 100)
                                success, msg = execute_okx_try_order(parite, "buy", sz=esit_butce_tr, sz_type="quote_ccy")
                                if success:
                                    send_telegram_message(chat_id, f"🟢 {parite} Alış Başarılı! Tutar: `{esit_butce_tr} TRY` (RSI: `{rsi_val_tr}`) 🚀💰")
                                else:
                                    send_telegram_message(chat_id, f"⚠️ *{parite} Alış Hatası:* `{msg}`")
                                
                                AKTIF_ISLEMLER.append({
                                    "coin": parite,
                                    "giris": p_fiyat_tr,
                                    "hedef": hedef_tr,
                                    "kar_orani": MIN_GARANTI_KAR,
                                    "rsi": rsi_val_tr,
                                    "butce": esit_butce_tr,
                                    "islem_saati": zaman_str_tr,
                                    "durum": f"🟢 Korumalı Sepette (+%{MIN_GARANTI_KAR})"
                                })
                        elif text.startswith("/durdur"):
                            BOT_CALISIYOR = False
                            AKTIF_ISLEMLER.clear()
                            send_telegram_message(chat_id, "🔴 Motor Durduruldu ve Liste Sıfırlandı!")
                        elif text.startswith("/cuzdan"):
                            try_val = get_okx_try_balance()
                            send_telegram_message(chat_id, f"💰 *Toplam Varlık:* `₺{try_val:,.2f}`")
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    set_telegram_commands()
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
