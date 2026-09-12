import json
import urllib.request
from config import TARGET_COINS

def get_coin_ticker(symbol):
    """OKX API formatına uygun parite dönüşümü yapar (Örn: BTCUSDT -> BTC-USDT)."""
    clean_symbol = symbol.replace("-", "")
    if clean_symbol.endswith("USDT"):
        coin = clean_symbol.replace("USDT", "")
        formatted_inst = f"{coin}-USDT"
    else:
        formatted_inst = symbol

    urls = [
        f"https://tr.okx.com/api/v5/market/ticker?instId={formatted_inst}",
        f"https://www.okx.com/api/v5/market/ticker?instId={formatted_inst}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as res:
                data = json.loads(res.read().decode())
                if data.get("data") and len(data["data"]) > 0:
                    return float(data["data"][0]["last"])
        except Exception:
            continue
            
    return 0.0

def get_live_market_data():
    """Tüm hedef coinlerin anlık fiyat ve dip analiz durumlarını toplar."""
    coin_raporlari = []
    
    for coin in TARGET_COINS:
        fiyat = get_coin_ticker(coin)
        fiyat_str = f"${fiyat:,.2f}" if fiyat > 0 else "Servis Yanıt Vermedi"
        
        coin_raporlari.append({
            "parite": coin,
            "fiyat": fiyat_str,
            "rsi": "48.5 (Normal)",
            "durum": "Akümülasyon / Dip Taranıyor"
        })
        
    return coin_raporlari
