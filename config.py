import os

# Tüm hassas bilgiler güvenli bir şekilde Render Environment'tan alınır
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

SYMBOLS = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
