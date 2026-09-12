    elif text == "/analiz":
        coinler = get_live_market_data()
        
        analiz_metni = (
            f"📈 *APEX CANLI PİYASA & DİP ANALİZİ*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
        )
        for c in coinler:
            analiz_metni += (
                f"🪙 *{c['parite']}*\n"
                f"   💰 Fiyat: `{c['fiyat']}` | RSI: `{c['rsi']}`\n"
                f"   📊 Durum: _{c['durum']}_\n\n"
            )
            
        analiz_metni += (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 *Dip Taraması:* Tüm Coinlerde 7/24 Aktif"
        )
        
        send_telegram(analiz_metni, chat_id)
