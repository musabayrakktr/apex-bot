import os

TELEGRAM_TOKEN = "8851186730:AAH5HyZBXPGwiuitUYagaq1dgcwte_fl34M"
CHAT_ID = "8982017587"

OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

# Şuan aktif olan pozisyonlar
ACTIVE_POSITIONS = [
    {"parite": "ETH/USDT", "yon": "LONG 🟢", "giris": "$2,450.00", "kar_zarar": "+%2.40"},
    {"parite": "SOL/USDT", "yon": "LONG 🟢", "giris": "$142.50", "kar_zarar": "+%0.85"}
]

# Geçmiş işlem hafızası
TRADE_HISTORY = [
    {"parite": "BTC/USDT", "islem": "KÂR 🟢", "tutar": "+1.25 USDT", "oran": "%1.2", "zaman": "12.09.2026 - 14:10"},
]
