import ccxt
import pandas as pd
import requests
import time
# ==========================================
# 1. BİLDİRİM VE BOT AYARLARI
# ==========================================
TELEGRAM_TOKEN = "8851186730:AAEVMnLsV9oh5PMEiw4K9eUWPrkW68z-WDc"
CHAT_ID = "8982017587"
def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram bağlantı hatası: {e}")
# ==========================================
# 2. BORSA VE PARAMETRE AYARLARI (COLAB ENGELİNİ AŞAN YAPILANDIRMA)
# ==========================================
# Google Colab ABD IP engelini aşmak için alternatif borsa bağlantısı
exchange = ccxt.kraken()  # Colab sunucu kısıtlamalarına takılmayan güvenilir borsa
symbol = 'BTC/USDT'
timeframe = '15m'
limit = 100
telegram_mesaj_gonder("🤖 *APEX* | Bağlantı Yenilendi. Sürekli Tarama Modu Aktif...")
# ==========================================
# 3. SÜREKLİ TARAMA DÖNGÜSÜ
# ==========================================
son_sinyal_durumu = None
while True:
    try:
        # Veri çekme ve analiz
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['Zaman', 'Açılış', 'Yüksek', 'Düşük', 'Kapanış', 'Hacim'])
        df['Zaman'] = pd.to_datetime(df['Zaman'], unit='ms')
        df['Direnç'] = df['Yüksek'].rolling(window=30).max()
        df['Destek'] = df['Düşük'].rolling(window=30).min()
        df['Ort_Hacim'] = df['Hacim'].rolling(window=20).mean()
        son_mum = df.iloc[-1]
        anlik_fiyat = son_mum['Kapanış']
        destek_seviyesi = son_mum['Destek']
        direnc_seviyesi = son_mum['Direnç']
        anlik_hacim = son_mum['Hacim']
        ort_hacim = son_mum['Ort_Hacim']
        destege_yakin_mi = abs(anlik_fiyat - destek_seviyesi) / destek_seviyesi < 0.005
        hacim_yuksek_mi = anlik_hacim > ort_hacim
        # Sinyal belirleme
        if destege_yakin_mi and hacim_yuksek_mi:
            mevcut_durum = "BUY"
            mesaj = (
                f"🟢 *OTOMATİK AL SİNYALİ (BUY / LONG)*\n"
                f"📍 *Parite:* BTC/USDT (15m)\n\n"
                f"🔹 *Giriş Fiyatı:* {anlik_fiyat} $\n"
                f"🛡️ *Destek (SL Bölgesi):* {destek_seviyesi} $\n"
                f"🎯 *Hedef (TP1):* {direnc_seviyesi} $\n"
                f"📊 *Hacim:* YÜKSEK (Onaylı)\n\n"
                f"⚡ *Aksiyon:* Destekten hacimli tepki alındı, alım değerlendirilebilir."
            )
        elif anlik_fiyat >= direnc_seviyesi * 0.995:
            mevcut_durum = "SELL"
            mesaj = (
                f"🔴 *OTOMATİK SAT SİNYALİ (SELL / SHORT)*\n"
                f"📍 *Parite:* BTC/USDT (15m)\n\n"
                f"🔸 *Giriş Fiyatı:* {anlik_fiyat} $\n"
                f"🧱 *Direnç Bölgesi:* {direnc_seviyesi} $\n"
                f"🎯 *Alt Hedef:* {destek_seviyesi} $\n\n"
                f"⚡ *Aksiyon:* Fiyat dirence dayandı, kâr satışı veya short değerlendirilebilir."
            )
        else:
            mevcut_durum = "NEUTRAL"
            mesaj = (
                f"🤖 *APEX | DURUM RAPORU*\n\n"
                f"📍 *BTC Fiyatı:* {anlik_fiyat} $\n"
                f"🛡️ *Destek:* {destek_seviyesi} $\n"
                f"🧱 *Direnç:* {direnc_seviyesi} $\n\n"
                f"⏳ *Durum:* Nötr. Fiyat aralıkta süzülüyor."
            )
        if mevcut_durum != son_sinyal_durumu or mevcut_durum in ["BUY", "SELL"]:
            telegram_mesaj_gonder(mesaj)
            son_sinyal_durumu = mevcut_durum
            print(f"[{time.strftime('%H:%M:%S')}] Bildirim gönderildi: {mevcut_durum}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Piyasa nötr, yeni bildirim atılmadı.")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    time.sleep(900)

