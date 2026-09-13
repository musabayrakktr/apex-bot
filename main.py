# /start ve /baslat Komutları
if text.startswith("/start") or text.startswith("/baslat"):
    welcome_text = (
        "🚀 *APEX TRADING BOT - KONTROL PANELİ* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Sistem güncellendi ve saatlik bildirimler aktif!\n\n"
        "💼 `/cuzdan` - OKX TR Cüzdan Bakiye Durumu\n"
        "📊 `/analiz` - Akıllı 5m & 15m Piyasa Analizi\n"
        "📈 `/rapor` - Geçmiş İşlemler ve Performans\n"
        "💱 `/kur` - Canlı Dolar ve BTC Kurları\n"
        "📜 `/gecmis` - Detaylı İşlem Dökümü\n"
        "🟢 `/calistir` - Oto Motoru Çalıştır\n"
        "🔴 `/durdur` - Oto Motoru Durdur"
    )
    send_telegram_message(chat_id, welcome_text)
