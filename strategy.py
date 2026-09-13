from market import get_okx_ticker

def analyze_market_for_dip(symbol):
    """
    TEST MODU: RSI eşiği esnetildi, otomatik test alımı tetikler.
    """
    try:
        ticker = get_okx_ticker(symbol)
        current_price = ticker.get("price", 100.0)
        
        # Test için RSI esnek tutuldu (Hemen alım yapması için)
        rsi = 48.5
        
        # RSI 55 altında olduğu için bot ANINDA alım tetikleyecek
        if rsi < 55:
            return True, current_price, rsi, "Test Alım Şartı Sağlandı"
            
        return False, current_price, rsi, "Normal Piyasa"
    except Exception as e:
        print(f"Strateji hatası: {e}")
        return False, 0.0, 50.0, "Hata"
