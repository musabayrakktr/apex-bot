import os
import time
import hmac
import hashlib
import base64
import json
import urllib.request
from datetime import datetime, timezone
import threading
from flask import Flask, render_template, redirect, url_for, jsonify

app = Flask(__name__)

AKTIF_ISLEMLER = [
    {"coin": "BTC-USDT", "giris": "77,350.00", "hedef": "78,500.00", "rsi_anlik": "42.5", "rsi_hedef": "65.0", "durum": "Takipte / Dip Bekleniyor"}
]

GECMIS_ISLEMLER = [
    {"coin": "ETH-USDT", "islem": "Alış/Satış", "kar": "+1.45%", "tutar": "+0.32 USDT", "zaman": "Dün 14:20"}
]


@app.route('/')
def home():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    try_val = usdt * dolar
    return render_template(
        'index.html',
        bot_durum=BOT_CALISIYOR,
        btc_fiyat=f"{btc:,.2f}",
        dolar_kur=f"{dolar:.2f}",
        usdt_bakiye=f"{usdt:,.2f}",
        try_bakiye=f"{try_val:,.2f}",
        aktif_islemler=AKTIF_ISLEMLER,
        gecmis_islemler=GECMIS_ISLEMLER
    )

@app.route('/api/data')
def api_data():
    btc, dolar = get_live_finans_data()
    usdt = get_okx_usdt_balance()
    return jsonify({
        "btc": f"{btc:,.2f}",
        "dolar": f"{dolar:.2f}",
        "usdt": f"{usdt:,.2f}"
    })

@app.route('/calistir_web')
def calistir_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = True
    send_telegram_message(ADMIN_ID, "🟢 *Web Panelden Tetiklendi:* RSI & Scalping Motoru Aktif! 🚀")
    return redirect(url_for('home'))

@app.route('/durdur_web')
def durdur_web():
    global BOT_CALISIYOR
    BOT_CALISIYOR = False
    send_telegram_message(ADMIN_ID, "🔴 *Web Panelden Tetiklendi:* Oto Motor Durduruldu!")
    return redirect(url_for('home'))

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8982017587))
OKX_API_KEY = os.environ.get("OKX_API_KEY", "")
OKX_SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "")
OKX_PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "")

BOT_CALISIYOR = False

STRATEJI_AYARLARI = {
    "takip_edilen_coinler": ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
    "min_islem_usdt": 1.0
}
