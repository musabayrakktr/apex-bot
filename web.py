from flask import Flask, request, jsonify
from telegram_bot import handle_telegram_message

app = Flask(__name__)

@app.route('/')
def home():
    return "Apex Bot 7/24 Aktif ve Çalışıyor! 🚀"

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """
    Telegram'dan gelen mesajları yakalayan uç nokta (Endpoint)
    """
    try:
        data = request.get_json()
        if data:
            handle_telegram_message(data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook Hatası: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
