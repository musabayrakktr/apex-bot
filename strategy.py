from market import get_live_market_data

# Aktif pozisyonları takip eden hafıza
active_positions = {}

def analyze_market_for_dip(symbol):
    """
    Hata korumalı, güvenli RSI Dip Stratejisi ve Kâr/Zarar Yönetimi
    """
    try:
        veriler = get_live_market_data()
        current_price = 100.0
        rsi = 50.0
        found = False

        # Gelen veriler içinde pariteyi güvenle ara
        for item in veriler:
            item_parite = str(item.get("parite", "")).replace("/", "").upper()
            target_symbol = symbol.replace("/", "").upper()
            
            if item_parite == target_symbol:
                # Fiyatı güvenli şekilde float'a çevir ($ ve virgül temizliği)
                raw_price = str(item.get("fiyat", "100.0")).replace("$", "").replace(",", "").strip()
                try:
                    current_price = float(raw_price)
                except ValueError:
                    current_price = 100.0

                # RSI değerini güvenli şekilde float'a çevir (metinleri ayıkla)
                raw_rsi = str(item.get("rsi", "50.0")).split()[0].replace(",", ".").strip()
                try:
                    rsi = float(raw_rsi)
                except ValueError:
                    rsi = 50.0
                
                found = True
                break

        if not found:
            return "HOLD", current_price, rsi, "Parite verisi bulunamadı, bekleniyor."

        # 1. Açık pozisyon varsa SATIŞ (Kâr Al / Stop Ol) kontrolü
        if symbol in active_positions:
            entry_price = active_positions[symbol]
            pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # %+2.5 Kâr Al veya %-1.5 Stop Ol
            if pnl_pct >= 2.5 or pnl_pct <= -1.5:
                del active_positions[symbol]
                return "SELL", current_price, rsi, f"Hedef/Stop ulaşıldı. Kâr/Zarar: %{pnl_pct:.2f}"
            
            return "HOLD", current_price, rsi, f"Pozisyonda Bekliyor (PNL: %{pnl_pct:.2f})"

        # 2. Pozisyon yoksa DİP (ALIM) kontrolü (RSI < 40 esnek eşik)
        if rsi < 40:
            active_positions[symbol] = current_price
            return "BUY", current_price, rsi, f"RSI Dip Kesişimi Gerçekleşti (RSI: {rsi:.1f})"

        return "HOLD", current_price, rsi, "Piyasa Nötr, Dip Bekleniyor"

    except Exception as e:
        print(f"Strateji Kritik Hata: {e}")
        return "HOLD", 100.0, 50.0, f"Hata: {str(e)}"
