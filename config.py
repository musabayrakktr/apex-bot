import os

# Telegram Konfigürasyonu
TELEGRAM_TOKEN = "8978911397:AAFIfqHHWiOEOSvosxVn6taHt5mfJOeGNNk"
CHAT_ID = os.environ.get("CHAT_ID", "6096537380")

# OKX API Konfigürasyonu
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")
IS_SIMULATION = not bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE)

# Strateji Parametreleri
COIN_BUDGET_TL = 250.0
MIN_PROFIT_TL = 1.0
TARGET_COINS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"]
SYMBOLS = TARGET_COINS

# Bellek Verileri
ACTIVE_POSITIONS = []
TRADE_HISTORY = []
COIN_PERFORMANCE = {}
