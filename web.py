from flask import Flask, render_template, jsonify
from market import get_live_finans_data
from telegram_bot import trading_active

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    btc, dolar = get_live_finans_data()
    usdt_val = 20.72
    try_val = round(usdt_val * dolar, 2)
    
    ai_data = [
        {
            "parite": "SOL/USDT", 
            "signal": "🟢 GÜÇLÜ YÜKSELİŞ SİNYALİ", 
            "confidence": "94.2", 
            "target": "$145.50", 
            "reason": "RSI 34 seviyesinden dip dönüşü gerçekleştirdi."
        },
        {
            "parite": "BTC/USDT", 
            "signal": "🟡 YATAY / TOPLAMA", 
            "confidence": "88.0", 
            "target": "$95,000", 
            "reason": "Destek bölgesinde hacim topluyor."
        },
        {
            "parite": "ETH/USDT", 
            "signal": "🟢 YÜKSELİŞ TRENDİ", 
            "confidence": "91.5", 
            "target": "$3,650", 
            "reason": "Kılavuz hareketli ortalama yukarı kesişti."
        }
    ]
    
    status_text = "🟢 7/24 Aktif" if trading_active else "🛑 Durduruldu"

    return jsonify({
        "usdt": f"{usdt_val:.2f}",
        "try": f"{try_val:,.2f}",
        "try_rate": f"{dolar:.2f}",
        "status": status_text,
        "ai": ai_data
    })
