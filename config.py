import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

# Senin Telegram ID'n güvenlik için ekleniyor
ADMIN_ID = 8982017587

SYMBOLS = ["SOL/USDT", "BTC/USDT", "ETH/USDT"]
