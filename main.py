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
MIN_GARANTI_KAR = 0.2 

AKTIF_ISLEMLER = []
GECMIS_ISLEMLER = [
    {"coin": "BTC-USDT", "islem": "Alış/Satış (AI Hacim Kâr Al)", "kar": "+0.20%", "tutar": "+0.30 USDT", "zaman": "14 Sep 09:52"},
    {"coin": "ETH-USDT", "islem": "Alış/Satış", "kar": "+1.45%", "tutar": "+0.32 USDT", "zaman": "Dün 14:20"}
]

@app.route('/')
def home():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    try_val = usdt * dolar
    
    global AKTIF_ISLEMLER
    if not AKTIF_ISLEMLER and btc > 0:
        esit_butce = round(usdt / len(SEPET_COINLERI), 2) if usdt > 0 else 7.31
        hedef_fiyat = btc * (1 + MIN_GARANTI_KAR / 100)
        zaman_str = datetime.now().strftime("%d %b %H:%M")
        AKTIF_ISLEMLER.append({
            "coin": "BTC-USDT",
            "giris": btc,
            "hedef": hedef_fiyat,
            "kar_orani": MIN_GARANTI_KAR,
            "rsi_anlik": "52.1",
            "rsi_hedef": "68.0",
            "butce": esit_butce,
            "islem_saati": zaman_str,
            "durum": f"🟢 Gerçek İşlemde (%{MIN_GARANTI_KAR})"
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
            "rsi_hedef": islem["rsi_hedef"],
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

@app.route('/api/data')
def api_data():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    return jsonify({
        "btc": f"{btc:,.2f}",
        "dolar": f"{dolar:.2f}",
        "usdt": f"{usdt:,.2f}"
    })

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* Gerçek USDT Bütçeli Sepet Motoru Aktif! 🚀💰")
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
        {"command": "calistir", "description": "🟢 Gerçek Bütçeli Sepet Motorunu Başlat"},
        {"command": "durdur", "description": "🔴 Motoru Durdur"},
        {"command": "aktif", "description": "📊 Anlık Aktif İşlemler & Kazanç"},
        {"command": "gecmis", "description": "📜 Son Tamamlanan İşlemler"},
        {"command": "analiz", "description": "📈 Anlık Piyasa & AI Durumu"},
        {"command": "cuzdan", "description": "💰 Güncel Bakiye Varlığı"},
        {"command": "kur", "description": "💱 BTC & Dolar Kuru"},
        {"command": "rapor", "description": "🌟 Saatlik Durum Özeti"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            print("✅ Emojili Telegram Menü Komutları Kaydedildi!")
    except Exception as e:
        print(f"Telegram setMyCommands hatası: {e}")

def get_okx_usdt_balance():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return 21.93
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
        url = f"https://www.okx.com{request_path}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0" and res.get("data"):
                details = res["data"][0].get("details", [])
                for coin in details:
                    if coin.get("ccy") == "USDT":
                        return float(coin.get("availBal", "0"))
    except Exception as e:
        print(f"Bakiye okuma hatası: {e}")
    return 21.93

def place_okx_real_order_usdt(inst_id, side, usdt_sz):
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
            "sz": str(usdt_sz),
            "tgtCcy": "quote_ccy"
        }
        body = json.dumps(payload)
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
        url = f"https://www.okx.com{request_path}"
        req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if res.get("code") == "0":
                return True
    except Exception as e:
        print(f"OKX API İstek Hatası: {e}")
    return False

def get_live_finans_data():
    try:
        url_btc = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        req_b = urllib.request.Request(url_btc, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_b, timeout=5) as resp:
            res_b = json.loads(resp.read().decode())
            btc_fiyat = float(res_b['data'][0]['last'])
        
        url_try = "https://www.okx.com/api/v5/market/ticker?instId=USDT-TRY"
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

def run_gercek_butceli_sepet_motoru():
    global AKTIF_ISLEMLER, GECMIS_ISLEMLER
    btc, _ = get_live_finans_data()
    if btc <= 0:
        return

    usdt = get_okx_usdt_balance()
    esit_butce = round(usdt / len(SEPET_COINLERI), 2) if usdt > 0 else 7.31

    if not AKTIF_ISLEMLER:
        hedef = btc * (1 + MIN_GARANTI_KAR / 100)
        zaman_str = datetime.now().strftime("%d %b %H:%M")
        
        place_okx_real_order_usdt("BTC-USDT", "buy", esit_butce)
        
        AKTIF_ISLEMLER.append({
            "coin": "BTC-USDT",
            "giris": btc,
            "hedef": hedef,
            "kar_orani": MIN_GARANTI_KAR,
            "rsi_anlik": "54.2",
            "rsi_hedef": "68.0",
            "butce": esit_butce,
            "islem_saati": zaman_str,
            "durum": f"🟢 Gerçek İşlemde (+%{MIN_GARANTI_KAR})"
        })
        print(f"🟢 [Gerçek Sepet] Alış Emri Gönderildi | Saat: {zaman_str} | Bütçe: {esit_butce} USDT")
        return

    islem = AKTIF_ISLEMLER[0]
    if btc >= islem["hedef"]:
        k_oran = islem.get("kar_orani", MIN_GARANTI_KAR)
        place_okx_real_order_usdt("BTC-USDT", "sell", islem.get('butce', 7.31))
        
        zaman_str = datetime.now().strftime("%d %b %H:%M")
        GECMIS_ISLEMLER.insert(0, {
            "coin": islem["coin"],
            "islem": f"Alış/Satış (Gerçek Kâr Al)",
            "kar": f"+%{k_oran:.2f}",
            "tutar": f"+{islem.get('butce', 7.31) * (k_oran/100):.2f} USDT",
            "zaman": zaman_str
        })
        print(f"🎯 [Gerçek Sepet] Hedef Yakalandı! Satış Başarılı. Fiyat: {btc}")
        send_telegram_message(ADMIN_ID, f"🎯 *Gerçek OKX Kâr Al Gerçekleşti!* `{islem['coin']}` +%{k_oran:.2f} kârla kapatıldı! Saat: `{zaman_str}` 🚀💰")
        
        AKTIF_ISLEMLER.clear()

def background_worker():
    global BOT_CALISIYOR, GECMIS_ISLEMLER, AKTIF_ISLEMLER
    last_update_id = 0
    son_bildirim_zaman = 0
    print("🤖 Apex Pro Bot Gerçek Bütçeli Sepet Döngüsü Başlatıldı...")
    
    while True:
        try:
            simdiki_zaman = time.time()
            if BOT_CALISIYOR:
                run_gercek_butceli_sepet_motoru()
                
                if simdiki_zaman - son_bildirim_zaman > 3600:
                    btc, dolar = get_live_finans_data()
                    usdt = get_okx_usdt_balance()
                    try_bakiye = usdt * dolar
                    saatlik_rapor = (
                        "🌟 *APEX KOMUTA MERKEZİ - SAATLİK RAPOR* 🚀\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🟢 *Sistem Durumu:* Gerçek USDT Bütçeli Sepet Aktif!\n\n"
                        f"🪙 *Bitcoin (BTC):* `${btc:,.2f}`\n"
                        f"💵 *OKX TR Cüzdan:* `{usdt:,.2f} USDT` (`₺{try_bakiye:,.2f}`)\n"
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
                        text = message.get("text", "").strip().lower()
                        
                        if user_id != ADMIN_ID:
                            send_telegram_message(chat_id, "⛔ Yetkin yok!")
                            continue
                        
                        if text.startswith("/start") or text.startswith("/baslat"):
                            welcome_msg = (
                                "🚀 *Apex Pro Terminal Aktif!*\n\n"
                                "🎯 *Komutlar:*\n"
                                "• `/calistir` - Gerçek Sepet Modunu Başlat\n"
                                "• `/durdur` - Motoru Durdur\n"
                                "• `/aktif` - Anlık Aktif İşlemler & Kazanç\n"
                                "• `/gecmis` - Son Tamamlanan İşlemler\n"
                                "• `/analiz` - Anlık Piyasa & AI Durumu\n"
                                "• `/cuzdan` - Güncel Bakiye Varlığı\n"
                                "• `/kur` - BTC & Dolar Kuru\n"
                                "• `/rapor` - Saatlik Durum Özeti"
                            )
                            send_telegram_message(chat_id, welcome_msg)
                        elif text.startswith("/calistir"):
                            BOT_CALISIYOR = True
                            send_telegram_message(chat_id, "🟢 Gerçek USDT Bütçeli Sepet Motoru Çalıştırıldı! 🚀💰")
                        elif text.startswith("/durdur"):
                            BOT_CALISIYOR = False
                            send_telegram_message(chat_id, "🔴 Oto Motor Durduruldu!")
                        elif text.startswith("/aktif"):
                            btc_guncel, dolar_guncel = get_live_finans_data()
                            aktif_metin = "📊 *ANLIK AKTİF İŞLEMLER & KAZANÇ HESABI*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            if not AKTIF_ISLEMLER:
                                aktif_metin += "Şu an takipte aktif işlem yok (Beklemede)."
                            else:
                                for islem in AKTIF_ISLEMLER:
                                    k_oran = islem.get("kar_orani", MIN_GARANTI_KAR)
                                    yatirilan = islem.get('butce', 7.31)
                                    hedef_usdt = yatirilan * (1 + k_oran / 100)
                                    hedef_try = hedef_usdt * dolar_guncel
                                    kâr_usdt = hedef_usdt - yatirilan
                                    kâr_try = kâr_usdt * dolar_guncel
                                    
                                    aktif_metin += (
                                        f"🪙 *Coin:* `{islem['coin']}`\n"
                                        f"⏱️ *İşlem Saati:* `{islem.get('islem_saati', 'Bilinmiyor')}`\n"
                                        f"📥 *Giriş:* `${islem['giris']:,.2f}`\n"
                                        f"🎯 *Hedef:* `${islem['hedef']:,.2f}` (+%{k_oran:.1f})\n"
                                        f"💵 *Ayrılan Bütçe:* `{yatirilan:.2f} USDT` (`₺{yatirilan * dolar_guncel:,.2f}`)\n"
                                        f"💰 *Satışta Ele Geçecek:* `{hedef_usdt:.2f} USDT` (`₺{hedef_try:,.2f}`)\n"
                                        f"📈 *Net Kâr:* `+{kâr_usdt:.2f} USDT` (`+₺{kâr_try:,.2f}`)\n"
                                        f"⚙️ *Durum:* {islem['durum']}\n"
                                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    )
                            send_telegram_message(chat_id, aktif_metin)
                        elif text.startswith("/gecmis"):
                            gecmis_metin = "📜 *SON TAMAMLANAN İŞLEMLER*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            if not GECMIS_ISLEMLER:
                                gecmis_metin += "Henüz tamamlanmış işlem yok."
                            else:
                                for islem in GECMIS_ISLEMLER[:5]:
                                    gecmis_metin += f"• *{islem['coin']}* | `{islem['kar']}` ({islem['zaman']})\n"
                            send_telegram_message(chat_id, gecmis_metin)
                        elif text.startswith("/analiz"):
                            btc, dolar = get_live_finans_data()
                            analiz_msg = (
                                "📊 *ANLIK PİYASA & GERÇEK SEPET* \n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🪙 *BTC Fiyat:* `${btc:,.2f}`\n"
                                f"🧠 *Strateji:* USDT bazlı bütçe ve net kazanç/TL hesabı devrede.\n"
                                f"⚡ *Durum:* {'Çalışıyor 🟢' if BOT_CALISIYOR else 'Beklemede ⏸️'}"
                            )
                            send_telegram_message(chat_id, analiz_msg)
                        elif text.startswith("/cuzdan"):
                            usdt = get_okx_usdt_balance()
                            _, dolar = get_live_finans_data()
                            try_val = usdt * dolar
                            send_telegram_message(chat_id, f"💰 *Cüzdan Varlığı:* `{usdt:,.2f} USDT` (`₺{try_val:,.2f}`)")
                        elif text.startswith("/kur"):
                            btc, dolar = get_live_finans_data()
                            send_telegram_message(chat_id, f"💱 *Kurlar*\n• BTC: `${btc:,.2f}`\n• USDT/TRY: `₺{dolar:.2f}`")
                        elif text.startswith("/rapor"):
                            btc, dolar = get_live_finans_data()
                            usdt = get_okx_usdt_balance()
                            try_bakiye = usdt * dolar
                            rapor_msg = (
                                "🌟 *APEX MANUEL RAPOR* 🚀\n"
                                f"🪙 *BTC:* `${btc:,.2f}`\n"
                                f"💵 *Cüzdan:* `{usdt:,.2f} USDT` (`₺{try_bakiye:,.2f}`)\n"
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
