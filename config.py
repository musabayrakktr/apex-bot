import os

# Telegram Konfigürasyonu
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7832675952:AAESn65y2K7iXkH_GqTjB0aO9vX_7m0_8v4")
CHAT_ID = os.environ.get("CHAT_ID", "6096537380")

# OKX API Konfigürasyonu (Gerçek Alım-Satım İçin)
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")
IS_SIMULATION = True  # API anahtarları girilene kadar güvenli simülasyon modunda çalışır

# Bütçe ve Strateji Parametreleri
COIN_BUDGET_TL = 250.0  # Coin başına ayrılan minimum bütçe (TL)
MIN_PROFIT_TL = 1.0     # İşlem başına hedeflenen minimum net kâr (TL)
TARGET_COINS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Hafıza Verileri (Aktif Pozisyonlar ve Geçmiş)
ACTIVE_POSITIONS = []
TRADE_HISTORY = []
COIN_PERFORMANCE = {coin: {"trades": 0, "profit": 0.0} for coin in TARGET_COINS}
