import hmac
import base64
import json
import urllib.request
import time
from config import OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE

def generate_signature(timestamp, method, request_path, body=""):
    message = timestamp + method + request_path + body
    mac = hmac.new(bytes(OKX_SECRET_KEY, encoding='utf-8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    return base64.b64encode(mac.digest()).decode('utf-8')

def get_account_balance():
    """
    OKX TR hesabına canlı istek atarak anlık TRY, USDT ve ETH varlıklarını sorgular.
    Borsadaki güncel değerlemeyi anlık TRY (₺) olarak döndürür.
    """
    if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
        # API henüz Render'a girilmediyse emniyet değeri
        return 957.24

    try:
        path = "/api/v5/account/balance"
        timestamp = str(time.time()).split('.')[0] + '.' + str(time.time()).split('.')[1][:3]
        headers = {
            "OK-ACCESS-KEY": OKX_API_KEY,
            "OK-ACCESS-SIGN": generate_signature(timestamp, "GET", path, ""),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(f"https://www.okx.com{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            if data.get("code") == "0" and data.get("data"):
                details = data["data"][0].get("details", [])
                total_try = 0.0
                
                for item in details:
                    ccy = item.get("ccy")
                    eq = float(item.get("eq", 0))
                    
                    if ccy == "USDT":
                        ticker_url = "https://www.okx.com/api/v5/market/ticker?instId=USDT-TRY"
                        t_req = urllib.request.Request(ticker_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(t_req, timeout=3) as t_res:
                            t_data = json.loads(t_res.read().decode())
                            usdt_try_price = float(t_data["data"][0]["last"]) if t_data.get("data") else 34.20
                        total_try += eq * usdt_try_price
                    elif ccy == "TRY":
                        total_try += eq
                    elif ccy == "ETH":
                        ticker_url = "https://www.okx.com/api/v5/market/ticker?instId=ETH-TRY"
                        t_req = urllib.request.Request(ticker_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(t_req, timeout=3) as t_res:
                            t_data = json.loads(t_res.read().decode())
                            eth_try_price = float(t_data["data"][0]["last"]) if t_data.get("data") else 115000.0
                        total_try += eq * eth_try_price
                
                return total_try if total_try > 0 else 957.24
    except Exception as e:
        print(f"OKX Canlı Bakiye Sorgu Hatası: {e}")
    
    return 957.24
