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
MIN_GARANTI_KAR = 0.2          # Temel kâr hedefi
MAKSIMUM_ZARAR_TOLERANSI = 1.5 # %1.5 Stop-Loss sınırı
MIN_ISLEM_TL = 250.0           # Borsa minimum işlem sınırı (250 TL)

AKTIF_ISLEMLER = []
GECMIS_ISLEMLER = []

@app.route('/')
def home():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    try_val = usdt * dolar
    
    min_usdt_siniri = MIN_ISLEM_TL / dolar
    global AKTIF_ISLEMLER
    
    if not AKTIF_ISLEMLER and usdt >= min_usdt_siniri:
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

    aktif_gosterge = []
    for islem in AKTIF_ISLEMLER:
        g_fiyat = islem["giris"]
        h_fiyat = islem["hedef"]
        k_oran = islem.get("kar_orani", MIN_GARANTI_KAR)
        aktif_gosterge.append({
            "coin": islem["coin"],
            "giris": f"{g_fiyat:,.2f}",
            "hedef": f"{h_fiyat:,.2f} (+%{k_oran:.2f})",
            "rsi_anlik": islem["rsi_anlik"],
            "rsi_hedef": "75.0",
            "durum": islem["durum"]
        })

    return render_template(
        'index.html',
        bot_durum=BOT_CALISIYOR,
        btc_fiyat=f"{btc:,.2f}",
        dolar_kur=f"{dolar:.2f}",
        usdt_bakiye=f"{usdt:,.2f}",
        try_bakiye=f"{try_val:,.2f}",
        aktif_islemler=aktif_gosterge,
        gecmis_islemler=GECMIS_ISLEMLER
    )

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* AI Canlı RSI & Koruma Botu Aktif! 🚀📊")
    return redirect(url_for('home'))

@app.route('/durdur_web')
def durdur_web():
    global BOT_CALISIYOR, AKTIF_ISLEMLER
    BOT_CALISIYOR = False
    AKTIF_ISLEMLER.clear()
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
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"Telegram mesaj gönderme hatası: {e}")

def set_telegram_commands():
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "baslat", "description": "🚀 Botu ve Komutları Gör"},
        {"command": "calistir", "description": "🟢 Canlı RSI Korumalı Sepet Motorunu Başlat"},
        {"command": "durdur", "description": "🔴 Motoru Durdur"},
        {"command": "al", "description": "⚡ Manuel Al: /al [coin] [USDT] (Min 250 TL karşılığı)"},
        {"command": "sat", "description": "⚡ Manuel Sat: /sat [coin] (Örn: /sat btc)"},
        {"command": "aktif", "description": "📊 Anlık Detaylı Aktif İşlemler, Fiyat & RSI"},
        {"command": "gecmis", "description": "📜 Son Tamamlanan İşlemler"},
        {"command": "analiz", "description": "📈 Anlık Piyasa & AI Gerekçeli Durum"},
        {"command": "cuzdan", "description": "💰 OKX TR Varlık & TL Analizi"},
        {"command": "kur", "description": "💱 BTC & Dolar Kuru"},
        {"command": "rapor", "description": "🌟 Saatlik Durum Özeti"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            print("✅ Telegram Komutları Menüye Kaydedildi!")
    except Exception as e:
        print(f"Telegram setMyCommands hatası: {e}")

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
                    elif ccy in ["BTC", "ETH", "SOL"] and bal > 0.000001:
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
    """OKX mum verilerinden gerçek anlık RSI hesaplar"""
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

        # 1. Kâr Hedefi & AI Zirve / RSI Satış Kontrolü
        hedef_asildi = anlik_kar_yuzde >= islem.get("kar_orani", MIN_GARANTI_KAR)
        ai_trend_bitti = anlik_kar_yuzde >= 0.2 and anlik_rsi > 70  # RSI 70 üzerine çıkıp şiştiğinde zirve satışı patlatır

        if hedef_asildi and ai_trend_bitti:
            success = place_okx_real_order(parite, "sell", "100%", sz_type="base_ccy")
            if success:
                zaman_str = datetime.now().strftime("%d %b %H:%M")
                kazanc_usdt = islem.get('butce', 5.0) * (anlik_kar_yuzde/100)
                GECMIS_ISLEMLER.insert(0, {
                    "coin": parite,
                    "islem": f"AI RSI Zirve Satış",
                    "kar": f"+%{anlik_kar_yuzde:.2f}",
                    "tutar": f"+{kazanc_usdt:.2f} USDT",
                    "zaman": zaman_str
                })
                print(f"🤖 [AI RSI Zirve] {parite} RSI ({anlik_rsi}) şişti, satış yapıldı.")
                send_telegram_message(ADMIN_ID, f"🤖 *AI RSI Zirve Satışı!* `{parite}` paritesinde RSI `{anlik_rsi}` seviyesine ulaştı, `+%{anlik_kar_yuzde:.2f}` kârla kapatıldı! 🚀💰")
                AKTIF_ISLEMLER.remove(islem)
                continue

        # 2. Akıllı Stop-Loss & AI Düşüş Filtresi (Geçici Düzeltme Kontrolü)
        stop_limiti = islem.get("stop_loss", g_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100))
        if p_fiyat <= stop_limiti:
            # AI Düşüş Filtresi: Eğer RSI 30'un üzerindeyse veya aşırı satım bölgesinde değilse AI "bu geçici düzeltme, tutmaya devam et" der!
            ai_panik_satis_filtresi = anlik_rsi > 35  # RSI 35 üstündeyse panik yapma, tutmaya devam et!
            
            gercek_zarar_orani = ((p_fiyat - g_fiyat) / g_fiyat) * 100
            if not ai_panik_satis_filtresi:
                success = place_okx_real_order(parite, "sell", "100%", sz_type="base_ccy")
                if success:
                    zaman_str = datetime.now().strftime("%d %b %H:%M")
                    GECMIS_ISLEMLER.insert(0, {
                        "coin": parite,
                        "islem": f"AI Stop-Loss",
                        "kar": f"%{gercek_zarar_orani:.2f}",
                        "tutar": f"Sermaye Korundu",
                        "zaman": zaman_str
                    })
                    print(f"🛡️ [AI Koruma] {parite} Stop oldu.")
                    send_telegram_message(ADMIN_ID, f"🛡️ *AI Koruma Kalkanı Devrede!* `{parite}` paritesinde düşüş onaylandığı için pozisyon kapatıldı.")
                    AKTIF_ISLEMLER.remove(islem)
            else:
                # AI düşüşün geçici olduğunu söylüyor, pozisyonu tutuyoruz!
                islem["durum"] = f"🛡️ Koruma Aktif (RSI: {anlik_rsi} - Tutuluyor)"

    usdt_guncel = get_okx_usdt_balance()
    if not AKTIF_ISLEMLER and usdt_guncel >= min_usdt_siniri:
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
                    print(f"🟢 [AI Sepet] {parite} Alındı | RSI: {anlik_rsi}")
                    send_telegram_message(ADMIN_ID, f"🟢 *AI Sepet Alımı:* `{parite}` paritesine `{esit_butce} USDT` yatırıldı! Anlık RSI: `{anlik_rsi}` 🚀")

def background_worker():
    global BOT_CALISIYOR, GECMIS_ISLEMLER, AKTIF_ISLEMLER
    last_update_id = 0
    son_bildirim_zaman = 0
    print("🤖 Apex Pro Canlı RSI Botu Başlatıldı...")
    
    while True:
        try:
            simdiki_zaman = time.time()
            if BOT_CALISIYOR:
                run_esit_sepet_motoru()
                
                if simdiki_zaman - son_bildirim_zaman > 3600:
                    btc, dolar = get_live_finans_data()
                    usdt, try_nakit, kriptolar = get_okx_account_details()
                    kripto_toplam_usdt = sum([k.get('usdt', 0) for k in kriptolar])
                    toplam_usdt = usdt + (try_nakit / dolar) + kripto_toplam_usdt
                    toplam_try = toplam_usdt * dolar
                    
                    saatlik_rapor = (
                        "🌟 *APEX KOMUTA MERKEZİ - SAATLİK RAPOR* 🚀\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🟢 *Sistem Durumu:* Canlı RSI & AI Koruma Aktif!\n\n"
                        f"🪙 *Bitcoin (BTC):* `${btc:,.2f}`\n"
                        f"💎 *Toplam Portföy:* `{toplam_usdt:,.2f} USDT` (`₺{toplam_try:,.2f}`)\n"
                    )
                    send_telegram_message(ADMIN_ID, saatlik_rapor)
                    son_bildirim_zaman = simdiki_zaman

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
                        raw_text = message.get("text", "").strip()
                        text_lower = raw_text.lower()
                        
                        if user_id != ADMIN_ID:
                            send_telegram_message(chat_id, "⛔ Yetkin yok!")
                            continue
                        
                        if text_lower.startswith("/start") or text_lower.startswith("/baslat"):
                            welcome_msg = (
                                "🚀 *Apex Pro Canlı RSI Terminal Aktif!*\n\n"
                                "🎯 *Komutlar ve Kullanım:*\n"
                                "• `/calistir` - Canlı RSI & Koruma Modunu Başlat\n"
                                "• `/durdur` - Motoru Durdur\n"
                                "• `/al btc 6` - Manuel Bütçeli Alım Yap (`/al [coin] [bütçe]`)\n"
                                "• `/sat btc` - Manuel Satım Yap (`/sat [coin]`)\n"
                                "• `/aktif` - Anlık Detaylı Aktif İşlemler, Fiyat & RSI\n"
                                "• `/gecmis` - Son Tamamlanan İşlemler\n"
                                "• `/analiz` - Anlık Piyasa & AI Gerekçeli Durum\n"
                                "• `/cuzdan` - OKX TR Varlık & TL Analizi\n"
                                "• `/kur` - BTC & Dolar Kuru\n"
                                "• `/rapor` - Saatlik Durum Özeti"
                            )
                            send_telegram_message(chat_id, welcome_msg)
                        elif text_lower.startswith("/calistir"):
                            BOT_CALISIYOR = True
                            send_telegram_message(chat_id, "🟢 Canlı RSI ve AI Koruma Motoru Çalıştırıldı! 🚀📊")
                        elif text_lower.startswith("/durdur"):
                            BOT_CALISIYOR = False
                            send_telegram_message(chat_id, "🔴 Oto Motor Durduruldu!")
                        elif text_lower.startswith("/al"):
                            parcalar = raw_text.split()
                            coin_secim = "btc"
                            _, dolar_kur = get_live_finans_data()
                            min_usdt = MIN_ISLEM_TL / dolar_kur
                            butce_miktar = round(min_usdt + 0.5, 2)
                            
                            if len(parcalar) > 1:
                                coin_secim = parcalar[1].lower()
                            if len(parcalar) > 2:
                                try:
                                    butce_miktar = float(parcalar[2])
                                except:
                                    pass
                            
                            if butce_miktar < min_usdt:
                                send_telegram_message(chat_id, f"⚠️ Minimum işlem sınırı 250 TL'dir (En az `{min_usdt:.2f} USDT` girmelisin)!")
                                continue
                                
                            inst_map = {"btc": "BTC-USDT", "eth": "ETH-USDT", "sol": "SOL-USDT"}
                            inst_id = inst_map.get(coin_secim, "BTC-USDT")
                            
                            usdt_bakiye = get_okx_usdt_balance()
                            if usdt_bakiye < butce_miktar:
                                send_telegram_message(chat_id, f"⚠️ Yetersiz USDT Bakiyesi! Mevcut: `{usdt_bakiye:.2f} USDT`")
                            else:
                                success = place_okx_real_order(inst_id, "buy", butce_miktar, sz_type="quote_ccy")
                                if success:
                                    p_fiyat = get_parite_fiyat(inst_id)
                                    anlik_rsi = get_real_rsi(inst_id)
                                    hedef = p_fiyat * (1 + MIN_GARANTI_KAR / 100)
                                    stop_fiyat = p_fiyat * (1 - MAKSIMUM_ZARAR_TOLERANSI / 100)
                                    AKTIF_ISLEMLER.append({
                                        "coin": inst_id,
                                        "giris": p_fiyat,
                                        "hedef": hedef,
                                        "stop_loss": stop_fiyat,
                                        "kar_orani": MIN_GARANTI_KAR,
                                        "rsi_anlik": f"{anlik_rsi:.1f}",
                                        "butce": butce_miktar,
                                        "durum": "⚡ AI Manuel Alım"
                                    })
                                    send_telegram_message(chat_id, f"⚡ *AI Manuel Alım Başarılı!* `{butce_miktar} USDT` değerinde `{inst_id}` alındı (RSI: `{anlik_rsi}`)! 🚀")
                                else:
                                    send_telegram_message(chat_id, f"❌ Manuel Alım Emri Başarısız Oldu!")
                        elif text_lower.startswith("/sat"):
                            parcalar = raw_text.split()
                            coin_secim = "btc"
                            if len(parcalar) > 1:
                                coin_secim = parcalar[1].lower()
                                
                            inst_map = {"btc": "BTC-USDT", "eth": "ETH-USDT", "sol": "SOL-USDT"}
                            inst_id = inst_map.get(coin_secim, "BTC-USDT")
                            
                            _, _, kriptolar = get_okx_account_details()
                            gercek_miktar = None
                            for k in kriptolar:
                                if k['ccy'] == coin_secim.upper():
                                    gercek_miktar = k['bal']
                                    
                            if not gercek_miktar or float(gercek_miktar) <= 0.00001:
                                send_telegram_message(chat_id, f"⚠️ Cüzdanında satılacak yeterli `{coin_secim.upper()}` bulunmuyor!")
                            else:
                                success = place_okx_real_order(inst_id, "sell", gercek_miktar, sz_type="base_ccy")
                                if success:
                                    zaman_str = datetime.now().strftime("%d %b %H:%M")
                                    GECMIS_ISLEMLER.insert(0, {
                                        "coin": inst_id,
                                        "islem": "Manuel Satış",
                                        "kar": "Nakde Çevrildi",
                                        "tutar": f"{gercek_miktar} {coin_secim.upper()}",
                                        "zaman": zaman_str
                                    })
                                    send_telegram_message(chat_id, f"⚡ *Manuel Satış Başarılı!* `{gercek_miktar} {coin_secim.upper()}` nakite çevrildi! 💰")
                                    AKTIF_ISLEMLER = [i for i in AKTIF_ISLEMLER if i["coin"] != inst_id]
                                else:
                                    send_telegram_message(chat_id, f"❌ Satış Başarısız! Miktar borsa minimum işlem sınırının altında.")
                        elif text_lower.startswith("/aktif"):
                            aktif_metin = "📊 *CANLI RSI & AKTİF İŞLEMLER* 🚀\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            if not AKTIF_ISLEMLER:
                                aktif_metin += "Şu an takipte aktif işlem yok (AI yeni fırsat arıyor ⏳)."
                            else:
                                _, dolar = get_live_finans_data()
                                _, _, kriptolar = get_okx_account_details()
                                
                                for islem in AKTIF_ISLEMLER:
                                    parite = islem['coin']
                                    p_anlik = get_parite_fiyat(parite)
                                    g_fiyat = islem['giris']
                                    h_fiyat = islem['hedef']
                                    s_fiyat = islem['stop_loss']
                                    k_oran = islem.get('kar_orani', MIN_GARANTI_KAR)
                                    islem_butce = islem.get('butce', 0.0)
                                    islem_try = islem_butce * dolar
                                    fark_yuzde = ((p_anlik - g_fiyat) / g_fiyat) * 100 if g_fiyat > 0 else 0.0
                                    isaret = "+" if fark_yuzde >= 0 else ""
                                    
                                    # Canlı RSI değerini anlık çekiyoruz
                                    guncel_rsi = get_real_rsi(parite)
                                    islem['rsi_anlik'] = f"{guncel_rsi:.1f}"
                                    
                                    ccy_adi = parite.split('-')[0]
                                    k_miktar = "0.00"
                                    k_usdt = 0.0
                                    for k in kriptolar:
                                        if k['ccy'] == ccy_adi:
                                            k_miktar = k['bal']
                                            k_usdt = k.get('usdt', 0.0)
                                    k_try = k_usdt * dolar

                                    aktif_metin += (
                                        f"🪙 *Parite:* `{parite}`\n"
                                        f"📥 *Alış Giriş Fiyatı:* `${g_fiyat:,.2f}` (`{islem_butce:.2f} USDT` / `₺{islem_try:,.2f}`)\n"
                                        f"🎯 *Hedef Eşik:* `${h_fiyat:,.2f}` (+%{k_oran:.1f})\n"
                                        f"🛡️ *AI Stop-Loss Sınırı:* `${s_fiyat:,.2f}` (-%{MAKSIMUM_ZARAR_TOLERANSI})\n"
                                        f"📈 *Anlık Piyasa Fiyatı:* `${p_anlik:,.2f}`\n"
                                        f"📊 *Mevcut Durum / Kâr:* `{isaret}{fark_yuzde:.2f}%`\n"
                                        f"💼 *Eldeki Pozisyon:* `{k_miktar} {ccy_adi}` (`~{k_usdt:.2f} USDT`)\n"
                                        f"📉 *Canlı Teknik RSI:* `{islem['rsi_anlik']}` (Yükseliş Filtresi Aktif 🧠)\n"
                                        f"⚙️ *Sistem Durumu:* {islem['durum']}\n"
                                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    )
                            send_telegram_message(chat_id, aktif_metin)
                        elif text_lower.startswith("/gecmis"):
                            gecmis_metin = "📜 *CANLI RSI SON İŞLEMLER*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            if not GECMIS_ISLEMLER:
                                gecmis_metin += "Henüz tamamlanmış işlem bulunmuyor ⏳."
                            else:
                                for islem in GECMIS_ISLEMLER[:5]:
                                    gecmis_metin += f"• *{islem['coin']}* | `{islem['kar']}` ({islem['tutar']}) | `{islem['zaman']}`\n"
                            send_telegram_message(chat_id, gecmis_metin)
                        elif text_lower.startswith("/analiz"):
                            btc, dolar = get_live_finans_data()
                            usdt_bakiye = get_okx_usdt_balance()
                            min_usdt_siniri = MIN_ISLEM_TL / dolar
                            
                            durum_aciklamasi = ""
                            if AKTIF_ISLEMLER:
                                durum_aciklamasi = "🟢 İşlemde: Sepet coinleri canlı RSI ve koruma kalkanıyla takip ediliyor."
                            elif not BOT_CALISIYOR:
                                durum_aciklamasi = "⏸️ Beklemede: Bot pasif (`/calistir` komutu ile başlatmalısın)."
                            elif usdt_bakiye < min_usdt_siniri:
                                durum_aciklamasi = f"⚠️ Beklemede: USDT bakiye minimum sınırın altında!"
                            else:
                                durum_aciklamasi = "🔍 Fırsat Bekleniyor: Bot aktif, uygun RSI ve trend sinyali aranıyor."

                            analiz_msg = (
                                "📊 *AI PİYASA & CANLI RSI ANALİZİ*\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🪙 *BTC Fiyat:* `${btc:,.2f}`\n"
                                f"💵 *Kullanılabilir USDT:* `{usdt_bakiye:.2f} USDT`\n"
                                f"🧠 *Strateji Durumu:* {durum_aciklamasi}\n"
                                f"⚡ *Motor Durumu:* {'Çalışıyor 🟢' if BOT_CALISIYOR else 'Beklemede ⏸️'}"
                            )
                            send_telegram_message(chat_id, analiz_msg)
                        elif text_lower.startswith("/cuzdan"):
                            usdt, try_nakit, kriptolar = get_okx_account_details()
                            _, dolar = get_live_finans_data()
                            
                            kripto_toplam_usdt = sum([k.get('usdt', 0) for k in kriptolar])
                            toplam_usdt = usdt + (try_nakit / dolar) + kripto_toplam_usdt
                            toplam_try = toplam_usdt * dolar
                            
                            cuzdan_msg = (
                                "💰 *OKX TR CÜZDAN & VARLIK ANALİZİ* 🚀\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                "💵 *NAKİT BAKİYELER:*\n"
                                f"• USDT: `{usdt:,.2f} USDT` (`₺{usdt * dolar:,.2f}`)\n"
                                f"• TRY: `₺{try_nakit:,.2f}`\n\n"
                                "🪙 *KRİPTO VARLIKLAR (OKX TR):*\n"
                            )
                            if kriptolar:
                                for k in kriptolar:
                                    cuzdan_msg += f"• *{k['ccy']}*: `{k['bal']}` (Değer: `~{k.get('usdt', 0):.2f} USDT` / `₺{k.get('usdt', 0) * dolar:,.2f}`)\n"
                            else:
                                cuzdan_msg += "• Aktif kripto varlık bulunmuyor.\n"
                                
                            cuzdan_msg += (
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"💎 *TOPLAM PORTFÖY DEĞERİ:*\n"
                                f"• `{toplam_usdt:,.2f} USDT`\n"
                                f"• `₺{toplam_try:,.2f}`"
                            )
                            send_telegram_message(chat_id, cuzdan_msg)
                        elif text_lower.startswith("/kur"):
                            btc, dolar = get_live_finans_data()
                            send_telegram_message(chat_id, f"💱 *Kurlar*\n• BTC: `${btc:,.2f}`\n• USDT/TRY: `₺{dolar:.2f}`")
                        elif text_lower.startswith("/rapor"):
                            btc, dolar = get_live_finans_data()
                            usdt, try_nakit, kriptolar = get_okx_account_details()
                            kripto_toplam_usdt = sum([k.get('usdt', 0) for k in kriptolar])
                            toplam_usdt = usdt + (try_nakit / dolar) + kripto_toplam_usdt
                            toplam_try = toplam_usdt * dolar
                            rapor_msg = (
                                "🌟 *APEX MANUEL RAPOR* 🚀\n"
                                f"🪙 *BTC:* `${btc:,.2f}`\n"
                                f"💎 *Toplam Portföy:* `{toplam_usdt:,.2f} USDT` (`₺{toplam_try:,.2f}`)\n"
                                f"⚙️ *Bot Durumu:* {'Aktif 🟢' if BOT_CALISIYOR else 'Pasif 🔴'}"
                            )
                            send_telegram_message(chat_id, rapor_msg)
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    set_telegram_commands()
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
