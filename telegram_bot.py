import time
import json
import urllib.request
from config import TELEGRAM_TOKEN, CHAT_ID

def send_telegram(message, target_chat_id=None):
    """Telegram mesajı gönderme fonksiyonu"""
    cid = target_chat_id if target_chat_id else CHAT_ID
    if not cid or not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": cid,
        "text": message,
        "parse_mode": "Markdown"
    }).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Telegram Gönderim Hatası: {e}")

def set_telegram_commands():
    """Telegram Menü Komutlarını Tanımlar"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Botu Başlat ve Menüyü Gör"},
        {"command": "cuzdan", "description": "Canlı Kasa & Bakiye Durumu"},
        {"command": "analiz", "description": "Coin Dip & Fiyat Analizi"},
        {"command": "rapor", "description": "Açık Pozisyonlar ve İşlem Geçmişi"},
        {"command": "baslat", "description": "Oto Alım-Satım Motorunu Çalıştır"},
        {"command": "stop", "description": "Oto Alım-Satım Motorunu Durdur"}
    ]
    payload = json.dumps({"commands": commands}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Set Commands Hatası: {e}")

def handle_message(text, chat_id):
    """Gelen komutları işler"""
    from trader import get_account_balance
    from market import get_live_market_data
    from config import ACTIVE_POSITIONS, TRADE_HISTORY

    cmd = text.lower().strip()

    if cmd in ['/start', 'start']:
        msg = (
            "⚡ *APEX TRADING BOT AKTİF!*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🤖 Botunuz OKX TR piyasasını 7/24 tarıyor.\n\n"
            "📌 *Komut Listesi:*\n"
            "💰 /cuzdan - Canlı Kasa Durumu\n"
            "📈 /analiz - Coin Dip Analizleri\n"
            "📊 /rapor - Pozisyonlar ve İşlem Geçmişi\n"
            "▶️ /baslat - Oto Motoru Çalıştır\n"
            "🛑 /stop - Oto Motoru Durdur"
        )
        send_telegram(msg, chat_id)

    elif cmd in ['/cuzdan', 'cuzdan']:
        b = get_account_balance()
        usdt = b.get("usdt", 20.72)
        try_rate = b.get("try_rate", 34.20)
        try_val = usdt * try_rate
        msg = (
            "💰 *CANLI KASA BAKIYESI*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *USDT Kasa:* `{usdt:,.2f} USDT`\n"
            f"₺ *TRY Karşılığı:* `₺{try_val:,.2f} TRY`\n"
            f"💱 *Dolar Kuru:* `₺{try_rate:.2f}`\n\n"
            "🔒 *Borsa:* OKX TR (Canlı Senkron)"
        )
        send_telegram(msg, chat_id)

    elif cmd in ['/analiz', 'analiz']:
        veriler = get_live_market_data()
        msg = "📈 *APEX CANLI PIYASA & DIP ANALIZI*\n━━━━━━━━━━━━━━━━━━━\n\n"
        for item in veriler:
            msg += f"🪙 *{item['parite']}*\n💰 Fiyat: `{item['fiyat']}` | RSI: `{item['rsi']}`\n📊 Durum: {item['durum']}\n\n"
        msg += "⏱️ *Dip Taraması: 7/24 Aktif*"
        send_telegram(msg, chat_id)

    elif cmd in ['/rapor', 'rapor']:
        msg = "📊 *İŞLEM & POZİSYON RAPORU*\n━━━━━━━━━━━━━━━━━━━\n\n"
        msg += f"🟢 *Açık Pozisyon Sayısı:* {len(ACTIVE_POSITIONS)}\n"
        for pos in ACTIVE_POSITIONS:
            msg += f"• {pos['parite']} - Giriş: {pos['giris']} ({pos['durum']})\n"
        msg += f"\n📜 *Tamamlanan İşlemler:* {len(TRADE_HISTORY)}\n"
        for th in TRADE_HISTORY[-5:]:
            msg += f"• {th['parite']} -> Kâr: {th['kar']} ({th['zaman']})\n"
        send_telegram(msg, chat_id)
