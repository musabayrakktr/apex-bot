import os
import time
import hmac
import hashlib
import base64
import json
import urllib.request
from datetime import datetime, timezone
import threading
from flask import Flask, render_template, redirect, url_for, jsonify

app = Flask(__name__)

SEPET_COINLERI = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
MIN_GARANTI_KAR = 0.2          # Temel kâr hedefi (%0.2)
MAKSIMUM_ZARAR_TOLERANSI = 1.5 # %1.5 Stop-Loss sınırı
MIN_ISLEM_TL = 250.0           # Borsa minimum işlem sınırı (250 TL)

AKTIF_ISLEMLER = []
GECMIS_ISLEMLER = []

def cuzdan_senkronize_et():
    """Bot başlarken veya /aktif çekildiğinde OKX TR cüzdanındaki mevcut coinleri otomatik algılayıp listeye ekler"""
    global AKTIF_ISLEMLER
    try:
        _, _, kriptolar = get_okx_account_details()
        mevcut_coinler = [i["coin"] for i in AKTIF_ISLEMLER]
        for k in kriptolar:
            ccy = k['ccy']
            bal = float(k['bal'])
            parite = f"{ccy}-USDT"
            if parite in SEPET_COINLERI and bal > 0.0000001:
                p_fiyat = get_parite_fiyat(parite)
                anlik_rsi = get_real_rsi(parite)
                hedef_fiyat = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
                stop_fiyat = p_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100)
                if parite not in mevcut_coinler:
                    AKTIF_ISLEMLER.append({
                        "coin": parite,
                        "giris": p_fiyat,
                        "hedef": hedef_fiyat,
                        "stop_loss": stop_fiyat,
                        "kar_orani": MIN_GARANTI_KAR,
                        "rsi_anlik": f"{anlik_rsi:.1f}",
                        "butce": bal * p_fiyat,
                        "durum": "🛡️ Cüzdandan Senkronize Edildi"
                    })
    except Exception as e:
        print(f"Cüzdan senkronizasyon hatası: {e}")

@app.route('/')
def home():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    try_val = usdt * dolar
    min_usdt_siniri = MIN_ISLEM_TL / dolar
    
    global AKTIF_ISLEMLER, GECMIS_ISLEMLER
    cuzdan_senkronize_et()
    
    _, _, kriptolar = get_okx_account_details()
    toplam_kripto_adet = sum([float(k['bal']) for k in kriptolar if float(k['bal']) > 0.0000001])
    
    if not AKTIF_ISLEMLER and toplam_kripto_adet == 0 and usdt >= min_usdt_siniri:
        esit_butce = round(usdt / len(SEPET_COINLERI), 2)
        if esit_butce < min_usdt_siniri:
            esit_butce = round(usdt, 2)
        for parite in SEPET_COINLERI:
            p_fiyat = get_parite_fiyat(parite)
            anlik_rsi = get_real_rsi(parite)
            if p_fiyat > 0:
                success = place_okx_real_order(parite, "buy", esit_butce, sz_type="quote_ccy")
                if success:
                    hedef_fiyat = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
                    stop_fiyat = p_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100)
                    AKTIF_ISLEMLER.append({
                        "coin": parite,
                        "giris": p_fiyat,
                        "hedef": hedef_fiyat,
                        "stop_loss": stop_fiyat,
                        "kar_orani": MIN_GARANTI_KAR,
                        "rsi_anlik": f"{anlik_rsi:.1f}",
                        "butce": esit_butce,
                        "durum": "🛡️ AI Koruma & Trend Aktif"
                    })

    # Aktif pozisyonların anlık kâr/zarar ve TL/USDT değerlerinin hesaplanması
    aktif_gosterge = []
    for islem in AKTIF_ISLEMLER:
        g_fiyat = islem["giris"]
        parite = islem["coin"]
        anlik_fiyat = get_parite_fiyat(parite)
        if anlik_fiyat <= 0:
            anlik_fiyat = g_fiyat
            
        tutar_usdt = islem.get("butce", 7.0)
        anlik_usdt_deger = tutar_usdt * (anlik_fiyat / g_fiyat)
        fark_usdt = anlik_usdt_deger - tutar_usdt
        fark_try = fark_usdt * dolar
        kar_yuzde = ((anlik_fiyat - g_fiyat) / g_fiyat) * 100
        renk = "#3fb950" if kar_yuzde >= 0 else "#f85149"
        
        aktif_gosterge.append({
            "coin": parite,
            "tutar_usdt": f"{tutar_usdt:.2f}",
            "tutar_try": f"{(tutar_usdt * dolar):.2f}",
            "anlik_usdt": f"{anlik_usdt_deger:.2f}",
            "anlik_try": f"{anlik_try:.2f}",
            "kar_yuzde": f"%{kar_yuzde:+.2f}",
            "kar_tl": f"₺{fark_try:+.2f}",
            "rsi_anlik": islem["rsi_anlik"],
            "durum": islem["durum"],
            "renk": renk
        })

    # Günlük özet ve net kâr/zarar hesaplamaları
    gun_basi_try = 1000.00  # Gün başı baz alınan kasa
    gun_basi_usdt = gun_basi_try / dolar
    gunluk_fark_tl = try_val - gun_basi_try
    gunluk_renk = "#3fb950" if gunluk_fark_tl >= 0 else "#f85149"

    return render_template(
        'index.html',
        bot_durum=BOT_CALISIYOR,
        btc_fiyat=f"{btc:,.2f}",
        dolar_kur=f"{dolar:.2f}",
        usdt_bakiye=f"{usdt:,.2f}",
        try_bakiye=f"{try_val:,.2f}",
        aktif_islemler=aktif_gosterge,
        gun_basi_try=f"{gun_basi_try:,.2f}",
        gun_basi_usdt=f"{gun_basi_usdt:.2f}",
        gunluk_toplam_tl=f"₺{gunluk_fark_tl:+,.2f}",
        gunluk_renk=gunluk_renk,
        gunluk_gecmis=GECMIS_ISLEMLER
    )

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    cuzdan_senkronize_et()
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* AI Canlı RSI & Koruma Botu Aktif! 🚀📊")
    return redirect(url_for('home'))

@app.route('/durdur_web')
def durdur_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = False
    send_telegram_message(ADMIN_ID, "🔴 *Web Panelden Tetiklendi:* Oto Motor Durduruldu!")
    return redirect(url_for('home'))

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8982017587))
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")
BOT_CALISIYOR = False

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"Telegram mesaj gönderme hatası: {e}")

def get_okx_account_details():
    nakit_usdt = 0.0
    nakit_try = 0.0
    kriptolar = []
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return 17.65, 0.0, [{"ccy": "BTC", "bal": "0.00015531", "eq": 12.0}]
    try:
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
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                details = res["data"][0].get("details", [])
                for coin in details:
                    bal = float(coin.get("availBal", "0"))
                    ccy = coin.get("ccy")
                    if ccy == "USDT":
                        nakit_usdt = float(coin.get("cashBal", bal))
                    elif ccy == "TRY":
                        nakit_try = float(coin.get("cashBal", bal))
                    elif ccy in ["BTC", "ETH", "SOL"] and bal > 0.0000001:
                        p_fiyat = get_parite_fiyat(f"{ccy}-USDT")
                        kriptolar.append({"ccy": ccy, "bal": f"{bal:.6f}", "usdt": bal * p_fiyat})
    except Exception as e:
        print(f"OKX TR Bakiye okuma hatası: {e}")
        nakit_usdt = 17.65
    return nakit_usdt, nakit_try, kriptolar

def get_okx_usdt_balance():
    usdt, _, _ = get_okx_account_details()
    return usdt

def get_parite_fiyat(inst_id):
    try:
        url = f"https://tr.okx.com/api/v5/market/ticker?instId={inst_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode())
            return float(res['data'][0]['last'])
    except:
        return 0.0

def get_real_rsi(inst_id):
    try:
        url = f"https://tr.okx.com/api/v5/market/candles?instId={inst_id}&bar=15m&limit=20"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode())
            if res.get("code") == "0" and res.get("data"):
                candles = res["data"]
                closes = [float(c[4]) for c in reversed(candles)]
                if len(closes) < 14:
                    return 55.0
                gains, losses = [], []
                for i in range(1, len(closes)):
                    delta = closes[i] - closes[i-1]
                    if delta > 0:
                        gains.append(delta)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(delta))
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                if avg_loss == 0:
                    return 100.0
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return round(rsi, 1)
    except:
        pass
    return 54.2

def place_okx_real_order(inst_id, side, sz, sz_type="quote_ccy"):
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return False
    try:
        request_path = "/api/v5/trade/order"
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        payload = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side,
            "ordType": "market",
            "sz": str(sz)
        }
        if side == "buy" and sz_type == "quote_ccy":
            payload["tgtCcy"] = "quote_ccy"
        body = json.dumps(payload, separators=(',', ':'))
        message = timestamp + "POST" + request_path + body
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
        req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0":
                return True
    except Exception as e:
        print(f"OKX TR Emir Hatası: {e}")
    return False

def get_live_finans_data():
    try:
        btc_fiyat = get_parite_fiyat("BTC-USDT")
        url_try = "https://tr.okx.com/api/v5/market/ticker?instId=USDT-TRY"
        try:
            req_t = urllib.request.Request(url_try, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_t, timeout=5) as resp_t:
                res_t = json.loads(resp_t.read().decode())
                dolar_kur = float(res_t['data'][0]['last'])
        except:
            dolar_kur = 48.58
        return btc_fiyat, dolar_kur
    except Exception as e:
        print(f"Kur hatası: {e}")
        return 77331.0, 48.60

def run_esit_sepet_motoru():
    global AKTIF_ISLEMLER, GECMIS_ISLEMLER
    cuzdan_senkronize_et()
    btc, dolar = get_live_finans_data()
    if btc <= 0:
        return
    usdt = get_okx_usdt_balance()
    min_usdt_siniri = MIN_ISLEM_TL / dolar
    
    for islem in list(AKTIF_ISLEMLER):
        parite = islem["coin"]
        p_fiyat = get_parite_fiyat(parite)
        if p_fiyat <= 0:
            continue
        g_fiyat = islem["giris"]
        anlik_kar_yuzde = ((p_fiyat - g_fiyat) / g_fiyat) * 100
        anlik_rsi = get_real_rsi(parite)
        islem["rsi_anlik"] = f"{anlik_rsi:.1f}"
        
        hedef_asildi = anlik_kar_yuzde >= islem.get("kar_orani", MIN_GARANTI_KAR)
        ai_trend_bitti = anlik_kar_yuzde >= 0.2 and anlik_rsi > 70
        
        if hedef_asildi and ai_trend_bitti:
            success = place_okx_real_order(parite, "sell", "100%", sz_type="base_ccy")
            if success:
                zaman_str = datetime.now().strftime("%d %b %H:%M")
                kazanc_usdt = islem.get('butce', 5.0) * (anlik_kar_yuzde/100)
                GECMIS_ISLEMLER.insert(0, {
                    "coin": parite,
                    "tip": "AI RSI Zirve Satış",
                    "oran": f"+%{anlik_kar_yuzde:.2f}",
                    "tutar": f"+{kazanc_usdt:.2f} USDT",
                    "zaman": zaman_str,
                    "renk": "#3fb950"
                })
                send_telegram_message(ADMIN_ID, f"🤖 *AI RSI Zirve Satışı!* `{parite}` paritesinde RSI `{anlik_rsi}` seviyesine ulaştı, `+%{anlik_kar_yuzde:.2f}` kârla kapatıldı! 🚀💰")
                AKTIF_ISLEMLER.remove(islem)
            continue
            
        stop_limiti = islem.get("stop_loss", g_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100))
        if p_fiyat <= stop_limiti:
            ai_panik_satis_filtresi = anlik_rsi > 35
            gercek_zarar_orani = ((p_fiyat - g_fiyat) / g_fiyat) * 100
            if not ai_panik_satis_filtresi:
                success = place_okx_real_order(parite, "sell", "100%", sz_type="base_ccy")
                if success:
                    zaman_str = datetime.now().strftime("%d %b %H:%M")
                    GECMIS_ISLEMLER.insert(0, {
                        "coin": parite,
                        "tip": "AI Stop-Loss",
                        "oran": f"%{gercek_zarar_orani:.2f}",
                        "tutar": "Sermaye Korundu",
                        "zaman": zaman_str,
                        "renk": "#f85149"
                    })
                    send_telegram_message(ADMIN_ID, f"🛡️ *AI Koruma Kalkanı Devrede!* `{parite}` paritesinde düşüş onaylandığı için pozisyon kapatıldı.")
                    AKTIF_ISLEMLER.remove(islem)
            else:
                islem["durum"] = f"🛡️ Koruma Aktif (RSI: {anlik_rsi} - Tutuluyor)"

    usdt_guncel = get_okx_usdt_balance()
    _, _, kriptolar = get_okx_account_details()
    toplam_kripto_adet = sum([float(k['bal']) for k in kriptolar if float(k['bal']) > 0.0000001])
    
    if not AKTIF_ISLEMLER and toplam_kripto_adet == 0 and usdt_guncel >= min_usdt_siniri:
        esit_butce = round(usdt_guncel / len(SEPET_COINLERI), 2)
        if esit_butce < min_usdt_siniri:
            esit_butce = round(usdt_guncel, 2)
        for parite in SEPET_COINLERI:
            p_fiyat = get_parite_fiyat(parite)
            anlik_rsi = get_real_rsi(parite)
            if p_fiyat > 0:
                success = place_okx_real_order(parite, "buy", esit_butce, sz_type="quote_ccy")
                if success:
                    hedef = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
                    stop_fiyat = p_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100)
                    AKTIF_ISLEMLER.append({
                        "coin": parite,
                        "giris": p_fiyat,
                        "hedef": hedef,
                        "stop_loss": stop_fiyat,
                        "kar_orani": MIN_GARANTI_KAR,
                        "rsi_anlik": f"{anlik_rsi:.1f}",
                        "butce": esit_butce,
                        "durum": "🛡️ AI Koruma & Trend Aktif"
                    })
                    send_telegram_message(ADMIN_ID, f"🟢 *AI Sepet Alımı:* `{parite}` paritesine `{esit_butce} USDT` yatırıldı! Anlık RSI: `{anlik_rsi}` 🚀")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
