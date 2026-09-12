import json
import urllib.request

def get_live_market_data():
    """BTC, Dolar, Gram Altın ve Çeyrek Altın verilerini 7/24 canlı API'lerden çeker"""
    
    # Varsayılan değerler
    btc_fiyat_str = "$62,450.00"
    dolar_str = "34.20 TL"
    gram_altin_str = "2,850.00 TL"
    ceyrek_altin_str = "4,680.00 TL"
    rsi_str = "48.5"
    trend_str = "Yatay Akümülasyon"

    # 1. OKX API'den Canlı BTC Fiyatı
    try:
        url_btc = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        req = urllib.request.Request(url_btc, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("code") == "0" and data.get("data"):
                last_price = float(data["data"][0]["last"])
                btc_fiyat_str = f"${last_price:,.2f}"
    except Exception as e:
        print(f"BTC fiyat çekme hatası: {e}")

    # 2. Canlı Dolar ve Döviz Kurları (Exchange Rate API)
    try:
        url_fx = "https://open.er-api.com/v6/latest/USD"
        req_fx = urllib.request.Request(url_fx, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_fx, timeout=5) as response_fx:
            fx_data = json.loads(response_fx.read().decode())
            if fx_data.get("result") == "success":
                usdtltry = fx_data["rates"].get("TRY", 0)
                if usdtltry > 0:
                    dolar_str = f"{usdtltry:.2f} TL"
                    
                    # 3. Gram ve Çeyrek Altın Hesaplama (Ons Altın + Dolar kuru üzerinden canlı hesap)
                    try:
                        url_gold = "https://data-asg.goldprice.org/dbjson/USD"
                        req_gold = urllib.request.Request(url_gold, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_gold, timeout=5) as response_gold:
                            gold_data = json.loads(response_gold.read().decode())
                            # Ons altın fiyatını alıyoruz
                            ounce_price_usd = float(gold_data["items"][0]["xauPrice"])
                            
                            # Gram Altın TL Fiyatı = (Ons / 31.1035) * Dolar Kuru
                            gram_try = (ounce_price_usd / 31.1035) * usdtltry
                            gram_altin_str = f"{gram_try:,.2f} TL"
                            
                            # Çeyrek Altın Yaklaşık Ağırlığı 1.75 gramdır
                            ceyrek_try = gram_try * 1.75
                            ceyrek_altin_str = f"{ceyrek_try:,.2f} TL"
                    except Exception as ge:
                        print(f"Altın hesaplama hatası: {ge}")
    except Exception as e:
        print(f"Dolar/Kur çekme hatası: {e}")

    return {
        "dolar": dolar_str,
        "gram_altin": gram_altin_str,
        "ceyrek_altin": ceyrek_altin_str,
        "btc_fiyat": btc_fiyat_str,
        "rsi": rsi_str,
        "trend": trend_str
    }
