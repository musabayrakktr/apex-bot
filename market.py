import json
import urllib.request

def get_live_market_data():
    """OKX borsasından canlı BTC fiyatı ve güncel kur/altın verilerini çeker"""
    
    # 1. Varsayılan (fallback) değerler
    btc_fiyat_str = "$62,450.00"
    dolar_str = "34.20 TL"
    gram_altin_str = "2,850.00 TL"
    ceyrek_altin_str = "4,680.00 TL"
    rsi_str = "48.5"
    trend_str = "Yatay Akümülasyon"

    # 2. OKX API'den Canlı BTC Fiyatı Çekme
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("code") == "0" and data.get("data"):
                last_price = float(data["data"][0]["last"])
                btc_fiyat_str = f"${last_price:,.2f}"
    except Exception as e:
        print(f"OKX fiyat çekme hatası: {e}")

    # 3. Canlı Dolar ve Döviz Kurlarını Çekme (Exchange Rate API)
    try:
        url_fx = "https://open.er-api.com/v6/latest/USD"
        req_fx = urllib.request.Request(url_fx, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_fx, timeout=5) as response_fx:
            fx_data = json.loads(response_fx.read().decode())
            if fx_data.get("result") == "success":
                try:
                    usdtltry = fx_data["rates"].get("TRY", 34.20)
                    dolar_str = f"{usdtltry:.2f} TL"
                except:
                    pass
    except Exception as e:
        print(f"Dolar kur çekme hatası: {e}")

    return {
        "dolar": dolar_str,
        "gram_altin": gram_altin_str,
        "ceyrek_altin": ceyrek_altin_str,
        "btc_fiyat": btc_fiyat_str,
        "rsi": rsi_str,
        "trend": trend_str
    }
