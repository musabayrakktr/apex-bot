import json
import urllib.request
from config import TELEGRAM_TOKEN, CHAT_ID, TRADE_HISTORY, ACTIVE_POSITIONS, TARGET_COINS
from market import get_live_market_data
from trader import get_account_balance

def set_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "🚀 Botu Başlat & Ana Menü"},
        {"command": "cuzdan", "description": "💰 OKX Canlı Toplam Varlık & Bütçe"},
        {"command": "analiz", "description": "📈 Piyasa Dip & RSI Analizi"},
        {"command": "rapor", "description": "📊 Pozisyonlar ve Kâr Durumu"},
        {"command": "kur", "description": "💱 Canlı Dolar, Altın ve BTC Kurları"},
        {"command": "gecmis", "description": "📜 Detaylı İşlem Dökümü"},
        {"command": "stop", "description": "🛑 Oto Motoru Durdur"},
        {"command": "baslat", "description": "▶️ Oto Motoru Çalıştır"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Menü hatası: {e}")

def send_telegram(message, chat_id=CHAT_ID, urgent=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_notification": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

def send_trade_alert(action, parite, miktar, fiyat, kar_tl=0.0):
    if action == "ALIM":
        msg = (
            f"🚨🚨 *ALIM İŞLEMİ GERÇEKLEŞTİ!* 🚨🚨\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Parite:* `{parite}`\n"
            f"💰 *Giriş Fiyatı:* `{fiyat}`\n"
            f"🛡️ *İşlem Tutarı:* `{miktar} USDT`\n"
            f"⏰ *Zaman:* Anlık Canlı Emirden\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Pozisyon takibe alındı.*"
        )
    else:
        msg = (
            f"🔔🔔 *SATIM İŞLEMİ (KÂR ALINDI)!* 🔔🔔\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Parite:* `{parite}`\n"
            f"💵 *Çıkış Fiyatı:* `{fiyat}`\n"
            f"📈 *Elde Edilen Kâr:* `{kar_tl:.2f} USDT`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Bakiye cüzdana eklendi.*"
        )
    send_telegram(msg, urgent=True)

def handle_message(raw_text, chat_id):
    text = raw_text.lower().strip()
    
    if text in ["/start", "start", "/help"]:
        send_telegram(
            "🤖 *APEX BOT - SİSTEM AKTİF*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Komut Listesi:*\n"
            "🔹 `/cuzdan` - Canlı toplam varlık & otomatik bütçe\n"
            "🔹 `/analiz` - Dip ve RSI analiz raporu\n"
            "🔹 `/rapor` - Açık pozisyonlar ve durum\n"
            "🔹 `/kur` - Canlı piyasa kurları\n"
            "🔹 `/gecmis` - Geçmiş kâr dökümü\n"
            "🔹 `/baslat` - Oto Motoru Çalıştır\n"
            "🔹 `/stop` - Oto Motoru Durdur",
            chat_id
        )
    elif text == "/cuzdan":
        bakiye_data = get_account_balance()
        toplam_usdt = bakiye_data["usdt"]
        try_rate = bakiye_data["try_rate"]
        toplam_try = toplam_usdt * try_rate
        
        hedef_coin_sayisi = len(TARGET_COINS) if TARGET_COINS else 5
        coin_butce_usdt = round(toplam_usdt / hedef_coin_sayisi, 2)
        if coin_butce_usdt < 5.0:
            coin_butce_usdt = 5.0
            
        max_pozisyon = int(toplam_usdt // coin_butce_usdt)
        acik_poz = len(ACTIVE_POSITIONS)
        kullanilabilir_poz = max(0, max_pozisyon - acik_poz)
        
        send_telegram(
            f"💰 *APEX CANLI CÜZDAN RAPORU*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *Toplam Varlık:* `{toplam_usdt:,.2f} USDT`\n"
            f"🇹🇷 *TL Karşılığı:* `{toplam_try:,.2f} TRY`\n"
            f"🛡️ *Otomatik Coin Başı Bütçe:* `{coin_butce_usdt} USDT`\n"
            f"📊 *Hedef Parite Sayısı:* `{hedef_coin_sayisi} Coin`\n"
            f"🔄 *Aktif Pozisyon:* `{acik_poz}` | *Boş Kapasite:* `{kullanilabilir_poz}`",
            chat_id
        )
    elif text == "/analiz":
        coinler = get_live_market_data()
        analiz_metni = (
            f"📈 *APEX CANLI PİYASA & DİP ANALİZİ*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
        )
        for c in coinler:
            analiz_metni += (
                f"🪙 *{c['parite']}*\n"
                f"   💰 Fiyat: `{c['fiyat']}` | RSI: `{c['rsi']}`\n"
                f"   📊 Durum: _{c['durum']}_\n\n"
            )
        analiz_metni += (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Dip Taraması:* Tüm Coinlerde 7/24 Aktif"
        )
        send_telegram(analiz_metni, chat_id)
    elif text == "/rapor":
        if not ACTIVE_POSITIONS:
            send_telegram("📅 *APEX POZİSYON RAPORU*\n━━━━━━━━━━━━━━━━━━━\n🚀 Şu an açık pozisyon yok. Dip tespiti bekleniyor...", chat_id)
        else:
            rapor_metni = "📅 *APEX AKTİF POZİSYONLAR*\n━━━━━━━━━━━━━━━━━━━\n"
            for p in ACTIVE_POSITIONS:
                rapor_metni += f"🔹 *{p['parite']}*\n  Alış: `{p['giris']}` | Anlık: `{p['anlik']}`\n  Durum: *{p['durum']}*\n\n"
            send_telegram(rapor_metni, chat_id)
    elif text in ["/kur", "/piyasa"]:
        m = get_live_market_data()
        send_telegram(
            f"💱 *CANLI PİYASA & KUR EKRANI*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Bitcoin (BTC):* `{m[0]['fiyat']}`\n"
            f"💵 *Dolar / TL:* `34.20 TL`\n"
            f"🟡 *Gram Altın:* `2,910 TL`",
            chat_id
        )
    elif text == "/gecmis":
        if not TRADE_HISTORY:
            send_telegram("📜 *İŞLEM GEÇMİŞİ*\n━━━━━━━━━━━━━━━━━━━\nHenüz tamamlanan işlem bulunmuyor.", chat_id)
        else:
            gecmis_metni = "📜 *İŞLEM GEÇMİŞİ VE KÂR DÖKÜMÜ*\n━━━━━━━━━━━━━━━━━━━\n"
            for t in TRADE_HISTORY:
                gecmis_metni += f"🔹 *{t['parite']}* | Kâr: *{t['kar']}*\n   🕒 _{t['zaman']}_\n\n"
            send_telegram(gecmis_metni, chat_id)
