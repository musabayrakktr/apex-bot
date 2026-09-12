import json
import urllib.request
from config import TELEGRAM_TOKEN, CHAT_ID, TRADE_HISTORY, ACTIVE_POSITIONS
from market import get_live_market_data
from trader import get_account_balance

def set_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "🚀 Botu Başlat & Ana Menü"},
        {"command": "cuzdan", "description": "💰 OKX Canlı Toplam Varlık"},
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

def send_telegram(message, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

def handle_message(raw_text, chat_id):
    text = raw_text.lower().strip()
    
    if text in ["/start", "start", "/help"]:
        send_telegram(
            "🤖 *APEX BOT - SİSTEM AKTİF*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Komut Listesi:*\n"
            "🔹 `/cuzdan` - Canlı toplam varlık & kapasite\n"
            "🔹 `/analiz` - Dip ve RSI analiz raporu\n"
            "🔹 `/rapor` - Açık pozisyonlar ve durum\n"
            "🔹 `/kur` - Canlı piyasa kurları\n"
            "🔹 `/gecmis` - Geçmiş kâr dökümü\n"
            "🔹 `/baslat` - Oto Motoru Çalıştır\n"
            "🔹 `/stop` - Oto Motoru Durdur",
            chat_id
        )
    elif text == "/cuzdan":
        bakiye_yaniti = get_account_balance()
        coin_butce_usdt = 10.0
        
        if isinstance(bakiye_yaniti, (int, float)):
            toplam_varlik_usdt = float(bakiye_yaniti)
            max_pozisyon = int(toplam_varlik_usdt // coin_butce_usdt)
            acik_poz = len(ACTIVE_POSITIONS)
            kullanilabilir_poz = max(0, max_pozisyon - acik_poz)
            
            send_telegram(
                f"💰 *APEX CANLI CÜZDAN RAPORU*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 *Toplam Varlık Değeri:* `{toplam_varlik_usdt:,.2f} USDT`\n"
                f"🛡️ *İşlem Başı Bütçe:* `{coin_butce_usdt} USDT`\n"
                f"📊 *Toplam Alım Kapasitesi:* `{max_pozisyon} Coin`\n"
                f"🔄 *Aktif Pozisyonda:* `{acik_poz}` | *Açılabilecek Boş:* `{kullanilabilir_poz}`",
                chat_id
            )
        else:
            send_telegram(f"💰 *APEX CANLI CÜZDAN RAPORU*\n━━━━━━━━━━━━━━━━━━━\n{bakiye_yaniti}", chat_id)

    elif text == "/analiz":
        m = get_live_market_data()
        send_telegram(
            f"📈 *APEX PİYASA ANALİZ RAPORU*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Parite:* BTC / USDT (5m)\n"
            f"💰 *Anlık Fiyat:* `{m['btc_fiyat']}`\n"
            f"📊 *RSI Durumu:* `{m['rsi']}`\n"
            f"📉 *Trend / Yön:* `{m['trend']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Dip Taraması:* Tüm Coinlerde 7/24 Aktif",
            chat_id
        )
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
            f"🪙 *Bitcoin (BTC):* `{m['btc_fiyat']}`\n"
            f"💵 *Dolar / TL:* `{m['dolar']}`\n"
            f"🟡 *Gram Altın:* `{m['gram_altin']}`\n"
            f"🪙 *Çeyrek Altın:* `{m['ceyrek_altin']}`",
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
