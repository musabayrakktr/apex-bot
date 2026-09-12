import os
import threading
import time
import json
import urllib.request
from flask import Flask, render_template_string

app = Flask(__name__)

# --- KEMİK BİLGİLER (SABİT) ---
TELEGRAM_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
CHAT_ID = "8982017587"

OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

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
        send_telegram("🤖 *Apex Bot İskelet Modunda Çalışıyor!*", chat_id)
    else:
        send_telegram(f"Mesaj alındı: {raw_text}", chat_id)

def telegram_polling_listener():
    offset = 0
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except: pass
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.loads(response.read().decode())
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            handle_message(update["message"].get("text", "").strip(), update["message"]["chat"]["id"])
        except: time.sleep(3)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>APEX PRO İskelet Terminal</title>
    <style>
        body { background-color: #0b0e14; color: #e1e7ec; font-family: sans-serif; text-align: center; padding-top: 50px; }
        h1 { color: #00f2fe; }
    </style>
</head>
<body>
    <h1>⚡ APEX PRO - SIFIRLANMIŞ İSKELET SİSTEM</h1>
    <p>Sunucu aktif, bağlantılar sağlam. Yeni stratejiyi inşa etmek için bekliyor.</p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

if __name__ == '__main__':
    threading.Thread(target=telegram_polling_listener, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
