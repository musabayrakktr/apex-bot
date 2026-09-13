import requests
import hmac
import hashlib
import base64
import time
from config import OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE

def get_okx_usdt_balance():
    """OKX TR hesabından canlı USDT bakiyesini çeker. API yoksa varsayılan veya 0 döner."""
    if not OKX_API_KEY or not OKX_SECRET_KEY or not OKX_PASSPHRASE:
        # API girilmediyse örnek canlı takip için standart değer veya test bakiye
        return 20.72 
    
    try:
        # OKX API V5 Balance Endpoint
        endpoint = "/api/v5/account/balance?ccy=USDT"
        url = f"https://www.okx.com{endpoint}"
        
        timestamp = str(int(time.time() * 1000))
        message = timestamp + "GET" + endpoint
        signature = hmac.new(
            OKX_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        sig_b64 = base64.b64encode(signature).decode('utf-8')
        
        headers = {
            "OK-ACCESS-KEY": OKX_API_KEY,
            "OK-ACCESS-SIGN": sig_b64,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
            "Content-Type": "application/json"
        }
        
        res = requests.get(url, headers=headers, timeout=5).json()
        if res.get("code") == "0":
            details = res['data'][0]['details']
            for d in details:
                if d['ccy'] == 'USDT':
                    return float(d['availBal']) # Kullanılabilir bakiye
        return 0.0
    except Exception as e:
        print(f"OKX Bakiye çekme hatası: {e}")
        return 20.72

def get_live_finans_data():
    """OKX üzerinden canlı BTC fiyatı ve USDT/TRY kurunu çeker."""
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        response = requests.get(url, timeout=5).json()
        btc_fiyat = float(response['data'][0]['last'])
        
        usdt_try_url = "https://www.okx.com/api/v5/market/ticker?instId=USDT-TRY"
        try:
            res_try = requests.get(usdt_try_url, timeout=3).json()
            dolar_kur = float(res_try['data'][0]['last'])
        except:
            dolar_kur = 48.58  # Yedek kur
            
        return btc_fiyat, dolar_kur
    except Exception as e:
        print(f"Kur çekme hatası: {e}")
        return 91400.0, 48.58
