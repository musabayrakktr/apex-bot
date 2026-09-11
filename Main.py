import os
import time
import threading
import requests
import ccxt
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 1. RENDER PORT DİNLEYİCİSİ ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"APEX Bot Full Al-Sat Canli!")

    def log_message(self, format, *args):
        return

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- 2. BOT VE OKX AYARLARI ---
TELEGRAM_BOT_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
TELEGRAM_CHAT_ID = "8982017587"

OKX_API_KEY = os.environ.get("OKX_API_KEY")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE")

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'XRP/USDT']
BUY_RSI_THRESHOLD = 30.0

exchange = ccxt.okx({
    'apiKey': OKX_API_KEY,
    'secret': OKX_SECRET_KEY,
    'password': OKX_PASSPHRASE,
    'enableRateLimit': True,
})

historical_rsi = {s: [] for s in SYMBOLS}
last_alert_status = {s: False for s in SYMBOLS}
bot_active = True

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def predict_trend(symbol_rsi_history):
    if len(symbol_rsi_history) < 3:
        return "🔮 Yön tespiti bekleniyor..."
    rsi_diff = symbol_rsi_history[-1] - symbol_rsi_history[-3]
    if symbol_rsi_history[-1] <= 35:
        return "🔮 DİP BÖLGESİ! Tepki yükselişi gelebilir."
    elif rsi_diff < -4:
        return f"🔮 DÜŞÜŞ İVMELENİYOR! RSI <= {BUY_RSI_THRESHOLD} olma ihtimali yüksek."
    elif rsi_diff > 4:
        return "🔮 YÜKSELİŞ İVMESİ! Fiyat yukarı gidiyor."
    else:
        return "🔮 YATAY SEYİR! Sakin piyasa."

def send_telegram_message(message, chat_id=TELEGRAM_CHAT_ID, disable_notification=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "disable_notification": disable_notification}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def set_telegram_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Botu başlat ve menüyü gör"},
        {"command": "stop", "description": "Otomatik Emir Alımını Durdur"},
        {"command": "baslat", "description": "Otomatik Emir Alımını Başlat"},
        {"command": "cuzdan", "description": "OKX Cüzdan Bakiyesini Gör"},
        {"command": "analiz", "description": "Akıllı RSI & Oto-Trade Raporu"},
        {"command": "rapor", "description": "Günlük Performans Özeti"},
        {"command": "alarmlar", "description": "Aktif Özel Fiyat Alarmları"},
        {"command": "btc", "description": "Bitcoin anlık durum"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except Exception as e:
        print(f"Komut set etme hatası: {e}")

def fetch_single_analysis(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=20)
        closes = [x[4] for x in ohlcv]
        rsi = calculate_rsi(closes)
        historical_rsi[symbol].append(rsi)
        if len(historical_rsi[symbol]) > 5:
            historical_rsi[symbol].pop(0)
        prediction = predict_trend(historical_rsi[symbol])
        return ticker['last'], rsi, prediction
    except Exception as e:
        print(f"{symbol} veri hatası: {e}")
        return None, None, None

def execute_order(symbol, side, amount):
    try:
        order = exchange.create_market_order(symbol, side, amount)
        return True, order
    except Exception as e:
        return False, str(e)

def background_market_scanner():
    global bot_active
    print("APEX Otomatik Tarayıcı Aktif...")
    time.sleep(15)
    while True:
        try:
            if bot_active:
                for s in SYMBOLS:
                    price, rsi, prediction = fetch_single_analysis(s)
                    if price is not None and rsi is not None:
                        coin_name = s.split('/')[0]
                        if rsi <= BUY_RSI_THRESHOLD and not last_alert_status[s]:
                            alert_msg = f"🚨 OTOMATİK DİP YAKALANDI!\n\n🪙 {coin_name}: {price:.2f} $\n📊 RSI: {rsi:.1f} (DİP!)\n{prediction}\n\n⚠️ İşlem aktif."
                            send_telegram_message(alert_msg)
                            last_alert_status[s] = True
                        elif rsi > (BUY_RSI_THRESHOLD + 5):
                            last_alert_status[s] = False
        except Exception as e:
            print(f"Tarayıcı hata: {e}")
        time.sleep(300)

def handle_updates():
    global bot_active
    set_telegram_commands()
    offset = 0
    print("APEX Dinleyici Çalışıyor...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    text = message.get("text", "").strip()
                    text_lower = text.lower()
                    chat_id = message.get("chat", {}).get("id")
                    
                    if not text or not chat_id:
                        continue
                        
                    if text_lower == "/start":
                        send_telegram_message("🤖 APEX FULL DONANIMLI YAYINDA!\n\nMenüden veya komutlardan dilediğin gibi işlem yapabilirsin kanka.", chat_id=chat_id)
                    
                    elif text_lower == "/stop":
                        bot_active = False
                        send_telegram_message("🛑 Otomatik emir alımı ve tarayıcı durduruldu.", chat_id=chat_id)
                    
                    elif text_lower == "/baslat":
                        bot_active = True
                        send_telegram_message("✅ Otomatik emir alımı ve tarayıcı yeniden başlatıldı!", chat_id=chat_id)
                    
                    elif text_lower in ["/analiz", "/rapor"]:
                        msg = "📡 APEX CANLI PİYASA & TAHMİN RAPORU\n\n"
                        for s in SYMBOLS:
                            price, rsi, prediction = fetch_single_analysis(s)
                            if price is not None:
                                msg += f"🪙 {s.split('/')[0]}: {price:.2f} $ | RSI: {rsi:.1f}\n{prediction}\n\n"
                            else:
                                msg += f"⚠️ {s} verisi alınamadı.\n\n"
                        send_telegram_message(msg, chat_id=chat_id)
                    
                    elif text_lower == "/cuzdan":
                        try:
                            balance = exchange.fetch_balance()
                            usdt_free = balance['total'].get('USDT', 0.0)
                            usdt_used = balance['used'].get('USDT', 0.0)
                            send_telegram_message(f"💼 OKX TR CÜZDAN BAKİYESİ\n\nKullanılabilir USDT: {usdt_free:.4f}\nİşlemdeki USDT: {usdt_used:.4f}", chat_id=chat_id)
                        except Exception as e:
                            send_telegram_message(f"⚠️ Cüzdan hatası: {e}", chat_id=chat_id)
                    
                    elif text_lower == "/btc":
                        price, rsi, prediction = fetch_single_analysis('BTC/USDT')
                        if price is not None:
                            send_telegram_message(f"🪙 BTC ANLIK DURUM\n\nFiyat: {price:.2f} $\nRSI: {rsi:.1f}\n{prediction}", chat_id=chat_id)
                        else:
                            send_telegram_message("⚠️ BTC verisi alınamadı.", chat_id=chat_id)
                    
                    elif text_lower == "/alarmlar":
                        status_str = "Aktif (Çalışıyor)" if bot_active else "Durduruldu"
                        send_telegram_message(f"🚨 AKTİF ALARMLAR\n\nEşik Değeri: RSI <= {BUY_RSI_THRESHOLD}\nDurum: {status_str}", chat_id=chat_id)
                    
                    elif text_lower.startswith("/al "):
                        parts = text.split()
                        if len(parts) == 3:
                            symbol, amount = parts[1].upper(), float(parts[2])
                            send_telegram_message(f"🔄 {symbol} için {amount} tutarında ALIM emri gönderiliyor...", chat_id=chat_id)
                            success, res = execute_order(symbol, 'buy', amount)
                            if success:
                                send_telegram_message(f"✅ BAŞARILI ALIM!\n\nEmir Detayı: {res.get('id', 'OK')}", chat_id=chat_id)
                            else:
                                send_telegram_message(f"❌ Alım başarısız: {res}", chat_id=chat_id)
                        else:
                            send_telegram_message("⚠️ Örnek kullanım: `/al BTC/USDT 0.001`", chat_id=chat_id)
                    
                    elif text_lower.startswith("/sat "):
                        parts = text.split()
                        if len(parts) == 3:
                            symbol, amount = parts[1].upper(), float(parts[2])
                            send_telegram_message(f"🔄 {symbol} için {amount} tutarında SATIM emri gönderiliyor...", chat_id=chat_id)
                            success, res = execute_order(symbol, 'sell', amount)
                            if success:
                                send_telegram_message(f"✅ BAŞARILI SATIM!\n\nEmir Detayı: {res.get('id', 'OK')}", chat_id=chat_id)
                            else:
                                send_telegram_message(f"❌ Satım başarısız: {res}", chat_id=chat_id)
                        else:
                            send_telegram_message("⚠️ Örnek kullanım: `/sat BTC/USDT 0.001`", chat_id=chat_id)
                            
        except Exception as e:
            print(f"Polling hata: {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    threading.Thread(target=background_market_scanner, daemon=True).start()
    threading.Thread(target=handle_updates, daemon=True).start()

    while True:
        time.sleep(10)
