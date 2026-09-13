from market import get_live_market_data

def analyze_market_for_dip(symbol):
    """
    TEST MODU: Koşulsuz anında test alımı tetikler.
    """
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 32.5  # Test alımı için sabitledik

        for item in veriler:
            # Sembol formatı uyumsuzluğu ihtimaline karşı kontrol
            if item.get("parite") in [symbol, symbol.replace("/", "")]:
                current_price = float(item.get("fiyat", 100.0))
                break

        # Her koşulda True dönecek
        return True, current_price, rsi, "Test Alım Şartı Sağlandı"
    except Exception as e:
        print(f"Strateji hatası: {e}")
        return True, 100.0, 30.0, "Hata Testi"
