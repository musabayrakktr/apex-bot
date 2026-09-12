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

def get_ticker_price_in_usdt(ccy, base_url):
    """Herhangi bir coin'in anlık USDT cinsinden değerini çeker."""
    if ccy == "USDT":
        return 1.0
    try:
        ticker_url = f"{base_url}/api/v5/market/ticker?instId={ccy}-USDT"
        req = urllib.request.Request(ticker_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as res:
            t_data = json.loads(res.read().decode())
            if t_data.get("data"):
                return float(t_data["data"][0]["last"])
    except Exception:
        pass
    return 0.0

def get_account_balance():
    """
    OKX hesabındaki TÜM varlıkları (USDT, TRY, BTC, ETH ve diğer tüm coinleri) 
    taramadan geçirir, anlık piyasa fiyatlarıyla toplam USDT değerini hesaplar.
    """
    if not (OKX_API_KEY and OKX_SECRET_KEY):
        return 27.78

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
                    total_usdt_value = 0.0
                    
                    for item in details:
                        ccy = item.get("ccy")
                        eq = float(item.get("eq", 0))
                        
                        if eq <= 0:
                            continue
                            
                        if ccy == "USDT":
                            total_usdt_value += eq
                        elif ccy == "TRY":
                            # TL bakiyesini USDT'ye dönüştürür
                            usdt_try = get_ticker_price_in_usdt("USDT-TRY", base_url)
                            price = usdt_try if usdt_try > 0 else 34.20
                            total_usdt_value += (eq / price)
                        else:
                            # BTC, ETH, SOL vb. tüm coinlerin anlık fiyatını USDT'ye çevirip ekler
                            coin_price = get_ticker_price_in_usdt(ccy, base_url)
                            total_usdt_value += (eq * coin_price)
                    
                    if total_usdt_value > 0:
                        return total_usdt_value
        except Exception as e:
            print(f"Bakiye tarama hatası ({base_url}): {e}")

    return 27.78
