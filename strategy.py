from market import get_live_market_data

# Aktif pozisyonları takip etmek için basit hafıza
active_positions = {}

def analyze_market_for_dip(symbol):
    """
    Gerçek RSI Dip Stratejisi + Kâr/Zarar (Satış) Yönetimi
    """
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 50.0

        for item in veriler:
            if item.get("parite") in [symbol, symbol.replace("/", "")]:
                raw_price = str(item.get("fiyat", "100.0")).replace("$", "").replace(",", "").strip()
                current_price = float(raw_price)
                rsi = float(item.get("rsi", 50.0))
                break

        # 1. Eğer bu paritede zaten açık pozisyonumuz varsa SATIŞ kontrolü yapalım
        if symbol in active_positions:
            entry_price = active_positions[symbol]
            pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # Kâr al (%2.5) veya Stop ol (%-1.5)
            if pnl_pct >= 2.5 or pnl_pct <= -1.5:
                # Pozisyonu kapat ve satış sinyali üret
                del active_positions[symbol]
                return "SELL", current_price, rsi, f"Hedef/Stop ulaşıldı. Kâr/Zarar: %{pnl_pct:.2f}"
            
            # Henüz satış şartı sağlanmadı, bekle
            return "HOLD", current_price, rsi, f"Pozisyonda Bekliyor (PNL: %{pnl_pct:.2f})"

        # 2. Pozisyon yoksa DİP (ALIM) arayalım (RSI < 38)
        if rsi < 38:
            active_positions[symbol] = current_price
            return "BUY", current_price, rsi, f"RSI Dip Kesişimi Gerçekleşti (RSI: {rsi:.1f})"

        return "HOLD", current_price, rsi, "Piyasa Nötr, Dip Bekleniyor"

    except Exception as e:
        print(f"Strateji hatası: {e}")
        return "HOLD", 100.0, 50.0, "Hata Durumu"
