import os
import threading
import time
import json
import urllib.request
from flask import Flask
from config import TELEGRAM_TOKEN, TARGET_COINS, ACTIVE_POSITIONS, TRADE_HISTORY
from telegram_bot import handle_message, set_telegram_commands, send_telegram
from strategy import analyze_market_for_dip
from web import render_dashboard

app = Flask(__name__)

IS_BOT_RUNNING = True

def auto_trading_engine():
    """7/24 Arka planda dip taraması yapan alım-satım motoru"""
    global IS_BOT_RUNNING
    print("🚀 Auto Trading Engine başlatıldı...")
    while True:
        try:
            if IS_BOT_RUNNING:
                for symbol in TARGET_COINS:
                    clean_symbol = symbol.replace("/", "-")
                    is_dip, current_price, rsi, reason = analyze_market_for_dip(clean_symbol)

                    existing_pos = next((p for p in ACTIVE_POSITIONS if p['parite'] == symbol), None)

                    if not existing_pos and is_dip:
                        new_pos = {
                            "parite": symbol,
                            "giris": f"${current_price:,.2f}",
                            "raw_giris": current_price,
                            "anlik": f"${current_price:,.2f}",
                            "durum": "Alım Yapıldı (Hedef Kâr Bekleniyor)"
                        }
                        ACTIVE_POSITIONS.append(new_pos)
                        send_telegram(
                            f"🚀 *ALIM İŞLEMİ GERÇEKLEŞTİ!*\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"🪙 *Parite:* {symbol}\n"
                            f"💰 *Alış Fiyatı:* `${current_price:,.2f}`\n"
                            f"📊 *RSI:* `{rsi:.1f}` (Dip Tespiti)\n"
                            f"🎯 *Bütçe:* 250 TL | Hedef: Mikro Kâr Satışı"
                        )
                    elif existing_pos:
                        buy_price = existing_pos["raw_giris"]
                        existing_pos["anlik"] = f"${current_price:,.2f}"

                        if current_price >= (buy_price * 1.004):
                            profit_usd = (current_price - buy_price) * (7.5 / buy_price)
                            profit_tl = profit_usd * 34.20
                            
                            ACTIVE_POSITIONS.remove(existing_pos)
                            TRADE_HISTORY.append({
                                "parite": symbol,
                                "kar": f"+{profit_tl:.2f} TL",
                                "zaman": time.strftime("%H:%M:%S")
                            })
                            
                            send_telegram(
                                f"💰 *KÂR İLE SATIŞ YAPILDI! (MİKRO SCALP)*\n"
                                f"━━━━━━━━━━━━━━━━━━━\n"
                                f"🪙 *Parite:* {symbol}\n"
                                f"💵 *Satış Fiyatı:* `${current_price:,.2f}`\n"
                                f"📈 *Elde Edilen Kâr:* `+{profit_tl:.2f} TL`\n"
                                f"✅ *Durum:* Kâr kasaya eklendi!"
                            )
                        elif current_price < buy_price:
                            existing_pos["durum"] = f"Şuan ${current_price:,.2f} (Zarar satışı yapılmıyor, yükseliş bekleniyor)"

            time.sleep(30)
        except Exception as e:
            print(f"Trading Engine hatası: {e}")
            time.sleep(10)

def telegram_polling_listener():
    """Telegram mesajlarını anında dinleyen motor"""
    global IS_BOT_RUNNING
    offset = 0
    
    # Eski webhook bağlantısını temizle
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
    except:
        pass

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
                            msg = update["message"]
                            text = msg.get("text", "").strip()
                            chat_id = msg.get("chat", {}).get("id")
                            if text and chat_id:
                                if text == "/stop":
                                    IS_BOT_RUNNING = False
                                    send_telegram("🛑 *Oto Alım-Satım Motoru Durduruldu!*", chat_id)
                                elif text == "/baslat":
                                    IS_BOT_RUNNING = True
                                    send_telegram("▶️ *Oto Alım-Satım Motoru Çalıştırıldı!*", chat_id)
                                else:
                                    handle_message(text, chat_id)
        except Exception as e:
            print(f"Polling hatası: {e}")
            time.sleep(3)

@app.route('/')
def home():
    return render_dashboard()

if __name__ == '__main__':
    try:
        set_telegram_commands()
    except Exception as e:
        print(f"Set commands hatası: {e}")

    t_tele = threading.Thread(target=telegram_polling_listener, daemon=True)
    t_tele.start()
    
    t_trade = threading.Thread(target=auto_trading_engine, daemon=True)
    t_trade.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
