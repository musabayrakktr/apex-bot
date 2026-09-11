import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 1. RENDER PORT DİNLEYİCİSİ ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"APEX Bot Canli!")

    def log_message(self, format, *args):
        return

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- 2. BOT AYARLARI ---
TELEGRAM_BOT_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
TELEGRAM_CHAT_ID = "8982017587"

# --- 3. TELGRAF DİNLEYİCİ VE KOMUTLAR ---
def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def handle_updates():
    offset = 0
    print("APEX Saf Polling Botu Başlatıldı...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")
                    
                    if not text or not chat_id:
                        continue
                        
                    if text == "/start":
                        send_telegram_message(chat_id, "🤖 APEX YAYINDA! Yapay zeka tahmin motoru ve saf altyapı aktif kanka.")
                    elif text == "/analiz":
                        send_telegram_message(chat_id, "📡 APEX CANLI PİYASA: Sistem stabil çalışıyor.")
                    elif text == "/cuzdan":
                        send_telegram_message(chat_id, "💼 OKX CÜZDAN: Bağlantı hazır.")
        except Exception as e:
            print(f"Polling döngü hatası: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # Sağlık sunucusunu arka planda başlat
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # Telegram dinleyicisini arka planda başlat
    threading.Thread(target=handle_updates, daemon=True).start()

    # Ana thread'i canlı tut
    while True:
        time.sleep(10)
