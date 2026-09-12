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

def get_ticker_price_in_usdt(ccy, base_url, headers_base):
    if ccy == "USDT":
        return 1.0
    try:
        ticker_url = f"{base_url}/api/v5/market/ticker?instId={ccy}-USDT"
        req = urllib.request.Request(ticker_url, headers=headers_base)
        with urllib.request.urlopen(req, timeout=3) as res:
            t_data = json.loads(res.read().decode())
            if t_data.get("data"):
                return float(t_data["data"][0]["last"])
    except Exception:
        pass
    return 0.0

def get_account_balance():
    if not (OKX_API_KEY and OKX_SECRET_KEY):
        return "⚠️ HATA: OKX_API_KEY veya OKX_SECRET_KEY Render'da bulunamadı!"

    path = "/api/v5/account/balance"
    timestamp = str(time.time()).split('.')[0] + '.' + str(time.time()).split('.')[1][:3]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": generate_signature(timestamp, "GET", path, ""),
        "OK-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }
    
    if OKX_PASSPHRASE:
        headers["OK-ACCESS-PASSPHRASE"] = OKX_PASSPHRASE

    base_urls = ["https://tr.okx.com", "https://www.okx.com"]
    hata_mesajlari = []
    
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
                            usdt_try = get_ticker_price_in_usdt("USDT-TRY", base_url, {"User-Agent": headers["User-Agent"]})
                            price = usdt_try if usdt_try > 0 else 34.20
                            total_usdt_value += (eq / price)
                        else:
                            coin_price = get_ticker_price_in_usdt(ccy, base_url, {"User-Agent": headers["User-Agent"]})
                            total_usdt_value += (eq * coin_price)
                    
                    return round(total_usdt_value, 2)
                else:
                    hata_mesajlari.append(f"{base_url} -> KOD: {data.get('code')} MSG: {data.get('msg')}")
        except Exception as e:
            hata_mesajlari.append(f"{base_url} -> Bağlantı Hatası: {str(e)}")

    return "⚠️ OKX BAGLANTI HATASI:\n" + "\n".join(hata_mesajlari)
