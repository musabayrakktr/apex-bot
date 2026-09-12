import json
import urllib.request
from config import TELEGRAM_TOKEN, CHAT_ID, TRADE_HISTORY
from market import get_live_market_data

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
            "🔹 `/piyasa` - Dolar, Gram ve Çeyrek Altın kurları\n"
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
    elif text == "/piyasa":
        m = get_live_market_data()
        send_telegram(
            f"🇪🇺🇹🇷 *CANLI PİYASA KURLARI*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Dolar / TL:* `{m['dolar']}`\n"
            f"🟡 *Gram Altın:* `{m['gram_altin']}`\n"
            f"🪙 *Çeyrek Altın:* `{m['ceyrek_altin']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Veri Kaynağı:* Anlık Takip Modülü",
            chat_id
        )
    elif text == "/gecmis":
        gecmis_metni = "📜 *GEÇMİŞ İŞLEM GEÇMİŞİ*\n━━━━━━━━━━━━━━━━━━━\n"
        for t in TRADE_HISTORY:
            gecmis_metni += f"🔹 *{t['parite']}* | {t['islem']} *{t['tutar']}* ({t['oran']})\n   🕒 _{t['zaman']}_\n\n"
        send_telegram(gecmis_metni, chat_id)
    else:
        send_telegram(f"Mesaj alındı: {raw_text}", chat_id)
