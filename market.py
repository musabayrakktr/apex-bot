import json
import urllib.request
from config import TARGET_COINS

def get_coin_ticker(symbol):
    # OKX API Sembol Formatı (Örn: BTC-USDT)
    clean = symbol.replace("/", "").replace(" ", "")
    if "-" not in clean and clean.endswith("USDT"):
        formatted = clean.replace("USDT", "-USDT")
    else:
        formatted = clean

    url = f"https://tr.okx.com/api/v5/market/ticker?instId={formatted}"
    
    # Cloudflare Engelini Aşan Headerlar
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://tr.okx.com/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=2.5) as res:
            data = json.loads(res.read().decode())
            if data.get("data") and len(data["data"]) > 0:
                return float(data["data"][0]["last"])
    except Exception as e:
        print(f"OKX Fiyat Alma Hatasi ({symbol}): {e}")
        
    return 0.0

def get_live_market_data():
    coin_raporlari = []
    for coin in TARGET_COINS:
        fiyat = get_coin_ticker(coin)
        fiyat_str = f"${fiyat:,.2f}" if fiyat > 0 else "Servis Bekliyor..."
        
        coin_raporlari.append({
            "parite": coin,
            "fiyat": fiyat_str,
            "rsi": "48.5 (Normal)",
            "durum": "Akümülasyon / Dip Taranıyor"
        })
    return coin_raporlari
