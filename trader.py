import time
from telegram_bot import send_telegram
from config import ACTIVE_POSITIONS, TRADE_HISTORY

def get_account_balance():
    return {
        "usdt": 20.72,
        "try_rate": 48.58
    }

def execute_buy_order(symbol, price, rsi):
    """Alım işlemini simüle eder ve Telegram'a bildirim gönderir"""
    pos = {
        "parite": symbol,
        "giris": price,
        "rsi": rsi,
        "durum": "Açık",
        "zaman": time.strftime("%H:%M:%S")
    }
    ACTIVE_POSITIONS.append(pos)
    
    msg = (
        f"🚀 *ALIM İŞLEMİ GERÇEKLEŞTİ!*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 *Parite:* `{symbol}`\n"
        f"💰 *Giriş Fiyatı:* `${price:,.2f}`\n"
        f"📊 *Alım RSI:* `{rsi}`\n"
        f"🎯 *Hedef Kâr:* `+%2.0`\n\n"
        f"🤖 *Bot Durumu:* Otomatik Takipte"
    )
    send_telegram(msg)
    return True
