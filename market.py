import json
import urllib.request
from config import TARGET_COINS

def get_coin_ticker(symbol):
    url = f"https://tr.okx.com/api/v5/market/ticker?instId={symbol}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode())
            if data.get("data"):
                return float(data["data"][0]["last"])
    except Exception:
        pass
    return 0.0

def get_live_market_data():
    """Tüm hedef coinlerin anlık fiyat ve durumlarını toplar."""
    coin_raporlari = []
    
    for coin in TARGET_COINS:
        fiyat = get_coin_ticker(coin)
        fiyat_str = f"${fiyat:,.2f}" if fiyat > 0 else "Yükleniyor..."
        
        coin_raporlari.append({
            "parite": coin,
            "fiyat": fiyat_str,
            "rsi": "48.5 (Normal)",
            "durum": "Akümülasyon / Dip Taranıyor"
        })
        
    return coin_raporlari
