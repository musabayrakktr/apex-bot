from market import get_live_market_data
from telegram_bot import send_telegram

# Kesişim bildirimlerinin üst üste spama dönüşmemesi için son sinyal takibi
LAST_SIGNALS = {}

def analyze_market_for_dip(symbol):
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 50.0

        for item in veriler:
            if item.get("parite") == symbol:
                current_price = float(item.get("fiyat", 100.0))
                rsi = float(item.get("rsi", 50.0))
                break

        target_rsi = 35.0  # Veya test modunda 55.0

        # Kesişim gerçekleşti mi?
        if rsi <= target_rsi:
            # Sadece yeni bir kesişim olduğunda Telegram bildirimi at
            if not LAST_SIGNALS.get(symbol, False):
                LAST_SIGNALS[symbol] = True
                msg = (
                    f"🎯 *APEX KESİŞİM SİNYALİ (ALIM FIRSATI)*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 *Parite:* `{symbol}`\n"
                    f"📊 *Anlık RSI:* `{rsi:.1f}` 📉\n"
                    f"🎯 *Hedef Alım Eşiği:* `{target_rsi}`\n"
                    f"⚡ *Durum:* _Kesişim Aşağı Yönlü Kırıldı! Dip Tespiti Onaylandı._\n\n"
                    f"🤖 *Bot alım emrini işleme koyuyor...*"
                )
                send_telegram(msg)

            return True, current_price, rsi, "Kesişim Onaylandı"
        else:
            LAST_SIGNALS[symbol] = False
            return False, current_price, rsi, "Kesişim Bekleniyor"

    except Exception as e:
        print(f"Strateji hatası: {e}")
        return False, 100.0, 50.0, "Hata"
