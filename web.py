from flask import render_template_string

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Apex Bot Terminal</title>
    <style>
        body { background-color: #0b0e14; color: #e1e7ec; font-family: sans-serif; text-align: center; padding-top: 50px; }
        h1 { color: #00f2fe; }
        .card { background: #161b22; display: inline-block; padding: 20px 40px; border-radius: 10px; border: 1px solid #30363d; margin-top: 20px; text-align: left; }
    </style>
</head>
<body>
    <h1>⚡ APEX BOT - MODÜLER PANEL</h1>
    <div class="card">
        <p><b>Sistem Durumu:</b> Aktif ve Stabil 🚀</p>
        <p><b>Mimari:</b> Modüler Parçalı Sistem (Config, Market, Telegram, Web)</p>
        <p><b>Sunucu:</b> Render / Flask Üzerinde Çalışıyor</p>
    </div>
</body>
</html>
"""

def render_dashboard():
    return render_template_string(DASHBOARD_HTML)
