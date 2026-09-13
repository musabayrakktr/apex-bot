import os
import threading
from telegram_bot import bot
from web import app

if __name__ == "__main__":
    print("🌟 Apex Bot Sıfırdan ve Kararlı Başlatılıyor...")
    
    # Telegram Botunu arka planda dinlemeye başlıyoruz
    def run_tg():
        print("🤖 Telegram Bot dinlemede...")
        bot.infinity_polling(skip_pending=True)

    t_tg = threading.Thread(target=run_tg, daemon=True)
    t_tg.start()

    # Flask Web Sunucusunu Render portuna bağlıyoruz
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
