from market import get_live_market_data

def analyze_market_for_dip(symbol):
    """
    TEST MODU: Otomatik alım tetikler.
    """
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 48.5

        for item in veriler:
            if item.get("parite") == symbol:
                current_price = float(item.get("fiyat", 100.0))
                rsi = float(item.get("rsi", 48.5))
                break

        # Test için RSI eşiği 55'in altında tutuldu
        if rsi < 55:
            return True, current_price, rsi, "Test Alım Şartı Sağlandı"
            
        return False, current_price, rsi, "Normal Piyasa"
    except Exception as e:
        print(f"Strateji hatası: {e}")
        return False, 100.0, 50.0, "Hata"
