import requests
import hmac
import hashlib
import base64
import time
from config import OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE

def get_okx_usdt_balance():
    """OKX TR hesabından canlı USDT bakiyesini çeker."""
    # Eğer API anahtarları girilmemişse test amaçlı veya senin bildiğin bakiye yerine 
    # gerçek durumu görmek için burayı kontrol ediyoruz.
    if not OKX_API_KEY or OKX_API_KEY == "BURAYA_API_KEY":
        print("⚠️ OKX API anahtarları eksik! config.py dosyasına anahtarlarını yazmalısın.")
        return 0.0  # Anahtar yoksa 0 döner, böylece API girmen gerektiğin anlarsın
    
    try:
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
        print(f"OKX API Yanıtı: {res}") # Loglarda hatayı net görelim diye
        
        if res.get("code") == "0":
            details = res['data'][0]['details']
            for d in details:
                if d['ccy'] == 'USDT':
                    return float(d['availBal'])
        return 0.0
    except Exception as e:
        print(f"OKX Canlı Bakiye Hatası: {e}")
        return 0.0

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
            dolar_kur = 48.58
            
        return btc_fiyat, dolar_kur
    except Exception as e:
        print(f"Kur çekme hatası: {e}")
        return 91400.0, 48.58
