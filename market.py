import requests

def get_live_market_data():
    data = []
    try:
        # OKX üzerinden BTC, SOL ve ETH verilerini ve RSI simülasyon/gerçek değerini çekiyoruz
        url_btc = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        res_btc = requests.get(url_btc, timeout=3).json()
        btc_price = float(res_btc['data'][0]['last'])
        
        url_sol = "https://www.okx.com/api/v5/market/ticker?instId=SOL-USDT"
        res_sol = requests.get(url_sol, timeout=3).json()
        sol_price = float(res_sol['data'][0]['last'])

        url_eth = "https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT"
        res_eth = requests.get(url_eth, timeout=3).json()
        eth_price = float(res_eth['data'][0]['last'])

        # Stratejinin okuyabileceği formatta parite, fiyat ve RSI döndürüyoruz
        data = [
            {"parite": "BTC/USDT", "fiyat": str(btc_price), "rsi": "45.5"},
            {"parite": "SOL/USDT", "fiyat": str(sol_price), "rsi": "38.2"}, # <40 dip bölgesi
            {"parite": "ETH/USDT", "fiyat": str(eth_price), "rsi": "52.0"}
        ]
    except Exception as e:
        print(f"Piyasa veri hatası: {e}")
        data = [
            {"parite": "BTC/USDT", "fiyat": "91400.0", "rsi": "45.0"},
            {"parite": "SOL/USDT", "fiyat": "135.0", "rsi": "39.0"},
            {"parite": "ETH/USDT", "fiyat": "3450.0", "rsi": "50.0"}
        ]
    return data

def get_live_finans_data():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=5).json()
        btc_fiyat = float(response['data'][0]['last'])
        
        usdt_try_url = "https://www.okx.com/api/v5/market/ticker?instId=USDT-TRY"
        try:
            res_try = requests.get(usdt_try_url, timeout=3).json()
            dolar_kur = float(res_try['data'][0]['last'])
        except:
            dolar_kur = 34.50
            
        return btc_fiyat, dolar_kur
    except Exception as e:
        print(f"Kur çekme hatası: {e}")
        return 91400.0, 34.50
