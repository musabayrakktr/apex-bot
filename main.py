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
