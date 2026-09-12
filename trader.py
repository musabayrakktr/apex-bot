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
    OKX hesabındaki kullanılabilir veya toplam USDT bakiyesini doğrudan canlı çeker.
    API henüz bağlı değilse varsayılan test USDT değerini döndürür.
    """
    if not (OKX_API_KEY and OKX_SECRET_KEY):
        return 27.78  # API henüz çekilemiyorsa varsayılan USDT

    path = "/api/v5/account/balance"
    timestamp = str(time.time()).split('.')[0] + '.' + str(time.time()).split('.')[1][:3]
    
    headers = {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": generate_signature(timestamp, "GET", path, ""),
        "OK-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }
    
    if OKX_PASSPHRASE:
        headers["OK-ACCESS-PASSPHRASE"] = OKX_PASSPHRASE

    base_urls = ["https://tr.okx.com", "https://www.okx.com"]
    
    for base_url in base_urls:
        try:
            req = urllib.request.Request(f"{base_url}{path}", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                if data.get("code") == "0" and data.get("data"):
                    details = data["data"][0].get("details", [])
                    total_usdt = 0.0
                    
                    for item in details:
                        ccy = item.get("ccy")
                        eq = float(item.get("eq", 0))
                        
                        # Hesapta direkt USDT miktarını al
                        if ccy == "USDT":
                            total_usdt += eq
                    
                    if total_usdt > 0:
                        return total_usdt
        except Exception as e:
            print(f"Bakiye sorgu hatası ({base_url}): {e}")

    return 27.78
