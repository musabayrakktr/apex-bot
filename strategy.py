from market import get_live_market_data

def analyze_market_for_dip(symbol):
    """
    TEST ALIMI MODU: Piyasa şartı ne olursa olsun anında test alımı tetikler.
    """
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 48.5

        for item in veriler:
            if item.get("parite") in [symbol, symbol.replace("/", "")]:
                current_price = float(item.get("fiyat", 100.0))
                rsi = float(item.get("rsi", 48.5))
                break

        # Test için anında alım verir
        return True, current_price, rsi, "Test Alım Sinyali (Zorunlu Alım)"
    except Exception as e:
        print(f"Strateji hatası: {e}")
        return True, 100.0, 45.0, "Test Zorunlu Alım"
