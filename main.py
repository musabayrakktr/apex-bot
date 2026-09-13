import os
import threading
from telegram_bot import bot
from web import app

if __name__ == "__main__":
    print("🌟 Apex Bot Başlatılıyor...")
    
    # Telegram Botunu polling ile başlatıyoruz
    def run_tg():
        try:
            print("🤖 Telegram Bot dinlemede...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Telegram Bot Polling Hatası: {e}")

    t_tg = threading.Thread(target=run_tg, daemon=True)
    t_tg.start()

    # Flask Web Sunucusunu Render portuna bağlıyoruz
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
