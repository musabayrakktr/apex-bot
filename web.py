from flask import Flask, render_template, jsonify
from market import get_live_market_data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    veriler = get_live_market_data()
    
    ai_predictions = []
    for item in veriler:
        parite = item.get("parite", "SOL/USDT")
        
        # Fiyattaki '$' ve ',' karakterlerini temizle
        raw_price = str(item.get("fiyat", "100.0")).replace("$", "").replace(",", "").strip()
        try:
            fiyat = float(raw_price)
        except ValueError:
            fiyat = 100.0
            
        # RSI değerinden ' (Normal)' gibi metinleri ayıkla ve sadece sayıyı al
        raw_rsi = str(item.get("rsi", "45.0")).split()[0].replace(",", ".").strip()
        try:
            rsi = float(raw_rsi)
        except ValueError:
            rsi = 45.0
            
        if rsi < 40:
            signal = "🚀 YÜKSELİŞ BEKLENTİSİ"
            confidence = round(85 + (40 - rsi) * 0.5, 1)
            target = f"${round(fiyat * 1.04, 2)}"
            reason = f"RSI {rsi:.1f} seviyesinde dipte. Güçlü tepki alımı bekleniyor."
        elif rsi > 65:
            signal = "🔻 DÜŞÜŞ / DÜZELTME"
            confidence = round(75 + (rsi - 65) * 0.4, 1)
            target = f"${round(fiyat * 0.96, 2)}"
            reason = f"RSI {rsi:.1f} aşırı alım bölgesinde. Kâr satışı riski yüksek."
        else:
            signal = "⚡ NÖTR / AKÜMÜLASYON"
            confidence = 65.0
            target = f"${round(fiyat * 1.01, 2)}"
            reason = f"RSI {rsi:.1f} yatay bantta. Kesişim ve dip sinyali bekleniyor."
            
        ai_predictions.append({
            "parite": parite,
            "signal": signal,
            "confidence": confidence,
            "target": target,
            "reason": reason
        })

    return jsonify({
        "usdt": 20.72,
        "try": 1006.58,
        "try_rate": 48.58,
        "bot_status": "Aktif",
        "ai": ai_predictions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
