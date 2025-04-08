def analyse_signaux(df):
    messages = []

    # Récupération des valeurs récentes
    derniere_val = df.iloc[-1]
    macd = derniere_val.get("macd")
    signal_macd = derniere_val.get("macd_signal")
    rsi = derniere_val.get("rsi")
    bb_lower = derniere_val.get("bb_lower")
    close = derniere_val.get("close")
    adx = derniere_val.get("adx")
    cci = derniere_val.get("cci")
    williams_r = derniere_val.get("williams_r")

    # Règles d'analyse combinée
    if macd is not None and signal_macd is not None:
        if macd > signal_macd:
            messages.append("📈 Le MACD vient de croiser au-dessus de sa ligne de signal. Cela peut indiquer un début de tendance haussière.")
        elif macd < signal_macd:
            messages.append("📉 Le MACD vient de croiser en dessous de sa ligne de signal. Cela peut indiquer une tendance baissière naissante.")

    if rsi is not None:
        if rsi < 30:
            messages.append("🟢 Le RSI est en dessous de 30 → actif survendu. Potentiel rebond à venir.")
        elif rsi > 70:
            messages.append("🔴 Le RSI dépasse 70 → actif potentiellement suracheté.")

    if close is not None and bb_lower is not None:
        if close < bb_lower:
            messages.append("📉 Le cours a franchi la bande inférieure de Bollinger. Possibilité de retournement à la hausse.")

    if adx is not None:
        if adx > 25:
            messages.append("💪 L'ADX est supérieur à 25 → tendance forte en cours.")
        elif adx < 20:
            messages.append("😴 L'ADX est faible → marché sans direction claire.")

    if cci is not None:
        if cci > 100:
            messages.append("📈 Le CCI indique une zone de surachat.")
        elif cci < -100:
            messages.append("📉 Le CCI indique une zone de survente.")

    if williams_r is not None:
        if williams_r < -80:
            messages.append("🟢 Williams %R < -80 → actif survendu.")
        elif williams_r > -20:
            messages.append("🔴 Williams %R > -20 → actif suracheté.")

    # Analyse combinée renforcée
    if rsi is not None and macd is not None and signal_macd is not None:
        if rsi < 30 and macd > signal_macd:
            messages.append("🚀 RSI bas + MACD haussier = Signal d'achat fort détecté !")
        elif rsi > 70 and macd < signal_macd:
            messages.append("⚠️ RSI élevé + MACD baissier = Potentiel retournement baissier !")

    if not messages:
        return "🤔 Aucun signal clair détecté pour le moment. Reste en alerte, les marchés bougent vite !"

    return "\n\n".join(messages)




