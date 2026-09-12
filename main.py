import os
from flask import Flask, render_template, jsonify
from trader import get_account_balance

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    bakiye_data = get_account_balance()
    toplam_usdt = bakiye_data.get("usdt", 20.72)
    try_rate = bakiye_data.get("try_rate", 34.20)
    toplam_try = toplam_usdt * try_rate
    
    return jsonify({
        "usdt": f"{toplam_usdt:,.2f}",
        "try": f"{toplam_try:,.2f}",
        "try_rate": f"{try_rate:.2f}"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
