import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "SENIN_TELEGRAM_TOKENIN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "SENIN_CHAT_IDN")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Telegram Gönderim Hatası: {e}")
        return None

def start_telegram_bot():
    print("🤖 Telegram Bot Servisi Aktif.")
