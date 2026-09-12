def set_telegram_commands():
    """Bot açıldığında Telegram sol alt menü komutlarını otomatik ayarlar"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    commands = [
        {"command": "cuzdan", "description": "OKX TR Cüzdan Bakiye Durumu"},
        {"command": "analiz", "description": "5m & 15m Piyasa Analiz Raporu"},
        {"command": "rapor", "description": "Geçmiş İşlemler ve Performans"},
        {"command": "kur", "description": "Canlı Dolar, Altın ve BTC Kurları"},
        {"command": "gecmis", "description": "Detaylı İşlem Dökümü"},
        {"command": "stop", "description": "Oto Motoru Durdur"},
        {"command": "baslat", "description": "Oto Motoru Çalıştır"}
    ]
    payload = {"commands": commands}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Menü ayarlama hatası: {e}")
