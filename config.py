import os

# Telegram Konfigürasyonu
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M")
CHAT_ID = os.environ.get("CHAT_ID", "6096537380")

# OKX API Konfigürasyonu (Render Environment Variables üzerinden okunur)
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

# API Keyler girildiyse otomatik CANLI moda geçer
IS_SIMULATION = not bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE)

# Strateji Parametreleri
COIN_BUDGET_TL = 250.0  # Pozisyon başına ayrılacak bütçe (TL)
MIN_PROFIT_TL = 1.0     # Hedeflenen minimum kâr (TL)
TARGET_COINS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]

# Bellek Verileri
ACTIVE_POSITIONS = []
TRADE_HISTORY = []
