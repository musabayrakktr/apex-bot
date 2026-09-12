import json
import urllib.request
import time
from config import ACTIVE_POSITIONS, TRADE_HISTORY, COIN_PERFORMANCE, MIN_PROFIT_TL, COIN_BUDGET_TL

def fetch_klines(symbol="BTC-USDT", bar="5m", limit=30):
    """OKX'ten son 5 dakikalık mum verilerini ve hacmi çeker"""
    try:
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={bar}&limit={limit}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            if data.get("code") == "0" and data.get("data"):
                # OKX formatı: [timestamp, open, high, low, close, volume, ...]
                return data["data"]
    except Exception as e:
        print(f"Kline verisi çekme hatası ({symbol}): {e}")
    return []

def calculate_rsi(prices, period=14):
    """Fiyat listesinden RSI göstergesini hesaplar"""
    if len(prices) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(abs(change))
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def analyze_market_for_dip(symbol="BTC-USDT"):
    """
    Son 5 dakikalık grafiği, RSI, Hacim ve Destek seviyelerini analiz eder.
    En dip noktayı tespit ettiğinde True döner.
    """
    klines = fetch_klines(symbol=symbol, bar="5m", limit=20)
    if not klines or len(klines) < 15:
        return False, 0.0, 50.0, "Yetersiz Veri"

    closes = [float(k[4]) for k in reversed(klines)]
    volumes = [float(k[5]) for k in reversed(klines)]
    current_price = closes[-1]

    rsi = calculate_rsi(closes)
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
    current_volume = volumes[-1]

    # Dip Şartları: RSI Aşırı Satım (RSI < 38), Fiyat en düşük seviyelere yakın ve Hacim canlı
    is_rsi_dip = rsi <= 38.0
    is_volume_spike = current_volume >= (avg_volume * 1.1)
    is_price_at_support = current_price <= (min(closes[:-1]) * 1.002)

    if is_rsi_dip and (is_volume_spike or is_price_at_support):
        return True, current_price, rsi, "🔥 En Dip Nokta Tespiti (Alım Fırsatı)"
    
    return False, current_price, rsi, "Düşüş Devam Ediyor / Dip Bekleniyor"
