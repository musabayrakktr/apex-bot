import json
import urllib.request
from config import TELEGRAM_TOKEN, CHAT_ID, TRADE_HISTORY, ACTIVE_POSITIONS
from market import get_live_market_data

def set_telegram_commands():
    """Bot açıldığında Telegram sol alt menü komutlarını emojili olarak ayarlar"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "cuzdan", "description": "💰 OKX TR Cüzdan Bakiye Durumu"},
        {"command": "analiz", "description": "📈 5m & 15m Piyasa Analiz Raporu"},
        {"command": "rapor", "description": "📊 Geçmiş İşlemler ve Performans"},
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
        print(f"Menü ayarlama hatası: {e}")

def send_telegram(message, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def handle_message(raw_text, chat_id):
    text = raw_text.lower()
    
    if text in ["/start", "start", "/help"]:
        send_telegram(
            "🤖 *APEX BOT - SİSTEM AKTİF*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Komut Listesi:*\n"
            "🔹 `/cuzdan` - Güncel bakiye durumu\n"
            "🔹 `/analiz` - 5m & 15m piyasa raporu\n"
            "🔹 `/rapor` - Günlük rapor & Aktif pozisyonlar\n"
            "🔹 `/kur` - Dolar, Altın ve BTC kurları\n"
            "🔹 `/gecmis` - Geçmiş işlem dökümü",
            chat_id
        )
    elif text == "/cuzdan":
        send_telegram(
            "💰 *APEX CÜZDAN RAPORU*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "💵 *Kasa (USDT):* `19.71 USDT`\n"
            "🛡️ *Durum:* Nakitte / Güvenli Bölgede",
            chat_id
        )
    elif text == "/analiz":
        m = get_live_market_data()
        send_telegram(
            f"📈 *APEX PİYASA ANALİZ RAPORU*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Parite:* BTC / USDT (5m & 15m)\n"
            f"💰 *Anlık Fiyat:* `{m['btc_fiyat']}`\n"
            f"📊 *RSI Durumu:* `{m['rsi']} (Nötr)`\n"
            f"📉 *Trend / Yön:* `{m['trend']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Durum:* Otomatik tarama aktif",
            chat_id
        )
    elif text == "/rapor":
        rapor_metni = "📅 *APEX GÜNLÜK İŞLEM RAPORU*\n━━━━━━━━━━━━━━━━━━━\n"
        rapor_metni += "🚀 *Şuan İşlemde Olan Coinler:*\n"
        for p in ACTIVE_POSITIONS:
            rapor_metni += f"🔹 *{p['parite']}* | {p['yon']} | Giriş: `{p['giris']}` | K/Z: *{p['kar_zarar']}*\n"
        rapor_metni += "\n🛡️ *Günlük Durum:* Bot stabil çalışıyor, risk yönetimi aktif."
        send_telegram(rapor_metni, chat_id)
    elif text in ["/kur", "/piyasa"]:
        m = get_live_market_data()
        send_telegram(
            f"💱 *CANLI PİYASA & KUR EKRANI*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Bitcoin (BTC):* `{m['btc_fiyat']}`\n"
            f"💵 *Dolar / TL:* `{m['dolar']}`\n"
            f"🟡 *Gram Altın:* `{m['gram_altin']}`\n"
            f"🪙 *Çeyrek Altın:* `{m['ceyrek_altin']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Veri Kaynağı:* Anlık Kur Takip Modülü",
            chat_id
        )
    elif text == "/gecmis":
        gecmis_metni = "📜 *GEÇMİŞ İŞLEM GEÇMİŞİ*\n━━━━━━━━━━━━━━━━━━━\n"
        for t in TRADE_HISTORY:
            gecmis_metni += f"🔹 *{t['parite']}* | {t['islem']} *{t['tutar']}* ({t['oran']})\n   🕒 _{t['zaman']}_\n\n"
        send_telegram(gecmis_metni, chat_id)
    else:
        send_telegram(f"Bilinmeyen komut: {raw_text}\nKomut listesi için /start yazabilirsin.", chat_id)
