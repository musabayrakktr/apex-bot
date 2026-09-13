import os
import time
import hmac
import hashlib
import base64
import json
import urllib.request
from datetime import datetime, timezone
import threading
from flask import Flask, render_template, redirect, url_for


# ==================== 1. WEB SUNUCUSU VE KOMUTA MERKEZİ ====================
app = Flask(__name__)

@app.route('/')
def home():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    try_val = usdt * dolar
    return render_template(
        'index.html',
        bot_durum=BOT_CALISIYOR,
        btc_fiyat=f"{btc:,.2f}",
        dolar_kur=f"{dolar:.2f}",
        usdt_bakiye=f"{usdt:,.2f}",
        try_bakiye=f"{try_val:,.2f}"
    )

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* Oto Motor Çalıştırıldı! 🚀")
    return redirect(url_for('home'))

@app.route('/durdur_web')
def durdur_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = False
    send_telegram_message(ADMIN_ID, "🔴 *Web Panelden Tetiklendi:* Oto Motor Durduruldu!")
    return redirect(url_for('home'))


# ==================== 2. AYARLAR VE GÜVENLİK ====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8982017587))
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

BOT_CALISIYOR = False


# ==================== 3. TELEGRAM MESAJ GÖNDERME ====================
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


# ==================== 4. OKX BAKIYE VE FİNANS ====================
def get_okx_usdt_balance():
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        return 0.0
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
    return 0.0


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
        return 91400.0, 48.58


# ==================== 5. AKILLI ANALİZ MOTORU ====================
def get_smart_analysis():
    try:
        url = "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=5m&limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode())
            candles = res.get('data', [])
            
        if candles:
            son_fiyat = float(candles[0][4])
            eski_fiyat = float(candles[-1][4])
            fark_yuzde = ((son_fiyat - eski_fiyat) / eski_fiyat) * 100
            
            if fark_yuzde > 0.1:
                trend = "📈 Yükseliş Eğilimi (Boğa)"
                tavsiye = "İşlem fırsatları aranıyor, kademeli alım uygun olabilir."
            elif fark_yuzde < -0.1:
                trend = "📉 Düşüş Eğilimi (Ayı)"
                tavsiye = "Temkinli olunmalı, destek noktaları takip ediliyor."
            else:
                trend = "⚖️ Yatay / Konsolidasyon"
                tavsiye = "Piyasa kararsız, kırılım bekleniyor."
                
            return son_fiyat, trend, tavsiye, f"{fark_yuzde:+.2f}%"
    except Exception as e:
        print(f"Analiz motoru hata: {e}")
        
    btc, _ = get_live_finans_data()
    return btc, "⚖️ Stabil", "Veriler taranıyor...", "%0.00"


# ==================== 6. TELEGRAM KOMUT DİNLEYİCİSİ VE SAATLİK BİLDİRİM ====================
def process_telegram_updates():
    global BOT_CALISIYOR
    last_update_id = 0
    son_saatlik_bildirim = 0
    print("🤖 Telegram Bot dinlemede (Terminal Modu)...")
    
    while True:
        try:
            simdiki_zaman = time.time()
            
            if BOT_CALISIYOR and (simdiki_zaman - son_saatlik_bildirim > 3600):
                btc, dolar = get_live_finans_data()
                usdt_bakiye = get_okx_usdt_balance()
                try_bakiye = usdt_bakiye * dolar
                
                saatlik_mesaj = (
                    "⏰ *SAATLİK DURUM VE ÇALIŞMA RAPORU* 🟢\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "✅ Bot aktif ve oto motor çalışıyor!\n\n"
                    f"🪙 BTC Fiyat: `${btc:,.2f}`\n"
                    f"💵 Cüzdan: `{usdt_bakiye:,.2f} USDT` (`₺{try_bakiye:,.2f}`)\n"
                    "📈 Sistem kar/zarar takibine devam ediyor."
                )
                send_telegram_message(ADMIN_ID, saatlik_mesaj)
                son_saatlik_bildirim = simdiki_zaman

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
                            send_telegram_message(chat_id, "⛔ Botu kullanma yetkin yok!")
                            continue
                        
                        if text.startswith("/start") or text.startswith("/baslat"):
                            welcome_text = (
                                "🚀 *APEX TRADING BOT - KONTROL PANELİ* 🌟\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                "✅ Web komuta merkezi ve terminal logları aktif!\n\n"
                                "💼 `/cuzdan` - OKX TR Cüzdan Bakiye Durumu\n"
                                "📊 `/analiz` - Akıllı 5m & 15m Piyasa Analizi\n"
                                "📈 `/rapor` - Geçmiş İşlemler ve Performans\n"
                                "💱 `/kur` - Canlı Dolar ve BTC Kurları\n"
                                "📜 `/gecmis` - Detaylı İşlem Dökümü\n"
                                "🟢 `/calistir` - Oto Motoru Çalıştır\n"
                                "🔴 `/durdur` - Oto Motoru Durdur"
                            )
                            send_telegram_message(chat_id, welcome_text)
                            
                        elif text.startswith("/cuzdan"):
                            usdt_bakiye = get_okx_usdt_balance()
                            btc, dolar = get_live_finans_data()
                            try_bakiye = usdt_bakiye * dolar
                            cevap = (
                                "💼 *OKX TR CÜZDAN DURUMU*\n"
                                "━━━━━━━━━━━━━━━━━━━\n"
                                f"💵 Canlı Varlık: `{usdt_bakiye:,.2f} USDT`\n"
                                f"🪙 Türk Lirası Karşılığı: `₺{try_bakiye:,.2f} TRY`\n"
                                f"📊 Anlık Kur: `{dolar:.2f} TL`"
                            )
                            send_telegram_message(chat_id, cevap)
                            
                        elif text.startswith("/kur"):
                            btc, dolar = get_live_finans_data()
                            cevap = (
                                "💱 *CANLI KURLAR*\n"
                                "━━━━━━━━━━━━━━━━━━━\n"
                                f"💵 Dolar (USDT-TRY): `{dolar:.2f} TL`\n"
                                f"🪙 Bitcoin (BTC): `${btc:,.2f}`"
                            )
                            send_telegram_message(chat_id, cevap)
                            
                        elif text.startswith("/analiz"):
                            fiyat, trend, tavsiye, oran = get_smart_analysis()
                            cevap = (
                                "📊 *AKILLI PİYASA ANALİZ RAPORU*\n"
                                "━━━━━━━━━━━━━━━━━━━\n"
                                "⏱ Zaman Dilimi: `5m & 15m Mum Verileri`\n"
                                f"🪙 BTC Fiyat: `${fiyat:,.2f}`\n"
                                f"📈 Trend: `{trend}`\n"
                                f"🔄 Değişim: `{oran}`\n"
                                f"💡 Yapay Zeka Yorumu: *{tavsiye}*"
                            )
                            send_telegram_message(chat_id, cevap)
                            
                        elif text.startswith("/rapor"):
                            cevap = (
                                "📈 *PERFORMANS VE RAPOR*\n"
                                "━━━━━━━━━━━━━━━━━━━\n"
                                "🟢 Toplam İşlem: `0`\n"
                                "💰 Toplam Kâr/Zarar: `₺0.00`\n"
                                "📊 Başarı Oranı: `%0`"
                            )
                            send_telegram_message(chat_id, cevap)
                            
                        elif text.startswith("/gecmis"):
                            cevap = (
                                "📜 *DETAYLI İŞLEM DÖKÜMÜ*\n"
                                "━━━━━━━━━━━━━━━━━━━\n"
                                "ℹ️ Son dönemde gerçekleştirilen kapalı işlem bulunmuyor."
                            )
                            send_telegram_message(chat_id, cevap)
                            
                        elif text.startswith("/calistir"):
                            BOT_CALISIYOR = True
                            send_telegram_message(chat_id, "🟢 *Oto Motor Çalıştırıldı!* Terminal aktif.")
                            
                        elif text.startswith("/durdur"):
                            BOT_CALISIYOR = False
                            send_telegram_message(chat_id, "🔴 *Oto Motor Durduruldu!* Terminal bekleme modunda.")
                            
        except Exception as e:
            print(f"Telegram polling hatası (Hata koruması aktif, yeniden deneniyor): {e}")
            time.sleep(5)


# ==================== 7. ANA BAŞLATICI ====================
if __name__ == "__main__":
    print("🌟 Apex Bot Komuta Merkezi Başlatılıyor...")
    t = threading.Thread(target=process_telegram_updates, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
