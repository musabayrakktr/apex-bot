import requests

def get_live_market_data():
    data = []
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        res = requests.get(url, timeout=3).json()
        btc_price = res['data'][0]['last']
        data.append({"parite": "BTC/USDT", "fiyat": btc_price})
        
        url_sol = "https://www.okx.com/api/v5/market/ticker?instId=SOL-USDT"
        res_sol = requests.get(url_sol, timeout=3).json()
        sol_price = res_sol['data'][0]['last']
        data.append({"parite": "SOL/USDT", "fiyat": sol_price})

        url_eth = "https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT"
        res_eth = requests.get(url_eth, timeout=3).json()
        eth_price = res_eth['data'][0]['last']
        data.append({"parite": "ETH/USDT", "fiyat": eth_price})
    except Exception as e:
        print(f"Piyasa veri hatası: {e}")
        data = [
            {"parite": "BTC/USDT", "fiyat": "91400.0"},
            {"parite": "SOL/USDT", "fiyat": "135.0"},
            {"parite": "ETH/USDT", "fiyat": "3450.0"}
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
