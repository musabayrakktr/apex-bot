from flask import render_template_string

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apex Bot | Professional Trading Terminal</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #0b0e14;
            color: #e1e7ec;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #21262d;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #00f2fe;
            font-size: 24px;
            letter-spacing: 1px;
        }
        .status-badge {
            background: rgba(35, 134, 54, 0.2);
            color: #3fb950;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            border: 1px solid rgba(63, 185, 80, 0.4);
            font-weight: 600;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .card h3 {
            color: #8b949e;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }
        .card p {
            font-size: 20px;
            font-weight: bold;
            color: #f0f6fc;
        }
        .terminal-box {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            font-family: 'Courier New', Courier, monospace;
        }
        .terminal-box h3 {
            color: #58a6ff;
            margin-bottom: 10px;
            font-size: 16px;
            font-family: 'Segoe UI', sans-serif;
        }
        ul {
            list-style-type: none;
        }
        li {
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
            font-size: 14px;
        }
        li:last-child {
            border-bottom: none;
        }
        .highlight { color: #3fb950; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ APEX BOT TERMINAL</h1>
            <div class="status-badge">● SİSTEM AKTİF</div>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Kasa Durumu</h3>
                <p>19.71 USDT</p>
            </div>
            <div class="card">
                <h3>Anlık BTC Fiyatı</h3>
                <p class="highlight">$62,450.00</p>
            </div>
            <div class="card">
                <h3>Modüler Altyapı</h3>
                <p style="color: #58a6ff; font-size: 16px;">Stabil & Ayrıştırılmış</p>
            </div>
        </div>

        <div class="terminal-box">
            <h3>🖥️ Sistem Logları & Aktif Durum</h3>
            <ul>
                <li>[INFO] Config modülü yüklendi ve sabitler tanımlandı.</li>
                <li>[INFO] Market veri servisi senkronize edildi.</li>
                <li>[INFO] Telegram bot polling dinleyicisi arka planda çalışıyor.</li>
                <li>[SUCCESS] Web arayüz paneli Render üzerinde başarıyla barındırılıyor.</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

def render_dashboard():
    return render_template_string(DASHBOARD_HTML)
