def analyse_signaux(df):
    messages = []
    score = 0

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
    sma_50 = derniere_val.get("sma_50")
    sma_200 = derniere_val.get("sma_200")

    # Détection de la tendance globale
    if sma_50 is not None and sma_200 is not None:
        if sma_50 > sma_200:
            messages.append("📈 Tendance globale haussière détectée (SMA50 > SMA200).")
        elif sma_50 < sma_200:
            messages.append("📉 Tendance globale baissière détectée (SMA50 < SMA200).")
        else:
            messages.append("⚖️ Les moyennes mobiles convergent. Tendance neutre.")

    # Règles d'analyse combinée
    if macd is not None and signal_macd is not None:
        if macd > signal_macd:
            messages.append("📈 Le MACD vient de croiser au-dessus de sa ligne de signal. Un regain d'élan haussier est possible.")
            score += 1
        elif macd < signal_macd:
            messages.append("📉 Le MACD est passé sous sa ligne de signal. Un essoufflement de la tendance pourrait se profiler.")
            score -= 1

    if rsi is not None:
        if rsi < 30:
            messages.append("🟢 Le RSI est en dessous de 30. L'actif semble survendu, un rebond pourrait survenir. Restez attentif.")
            score += 1
        elif rsi > 70:
            messages.append("🔴 Le RSI dépasse 70. Prudence, nous sommes peut-être en zone de surachat.")
            score -= 1

    if close is not None and bb_lower is not None:
        if close < bb_lower:
            messages.append("📉 Le cours a franchi la bande inférieure de Bollinger. Cela pourrait signaler une opportunité à la hausse, si confirmé par d'autres indicateurs.")
            score += 1

    if adx is not None:
        if adx > 25:
            messages.append("💪 L'ADX est au-dessus de 25. Cela renforce l’idée d’une tendance bien installée.")
            score += 1
        elif adx < 20:
            messages.append("😴 L'ADX est faible. Le marché est probablement en consolidation, sans direction forte.")
            score -= 1

    if cci is not None:
        if cci > 100:
            messages.append("📈 Le CCI indique une zone de surachat. Peut-être un excès d’enthousiasme ?")
            score -= 1
        elif cci < -100:
            messages.append("📉 Le CCI montre une zone de survente. Un retournement haussier pourrait s’esquisser.")
            score += 1

    if williams_r is not None:
        if williams_r < -80:
            messages.append("🟢 Williams %R < -80. L’actif est profondément survendu.")
            score += 1
        elif williams_r > -20:
            messages.append("🔴 Williams %R > -20. L’actif est suracheté, vigilance.")
            score -= 1

    # Analyse combinée renforcée
    if rsi is not None and macd is not None and signal_macd is not None:
        if rsi < 30 and macd > signal_macd:
            messages.append("🚀 Un signal puissant ! Le RSI bas combiné à un MACD haussier pourrait indiquer un excellent point d'entrée.")
            score += 2
        elif rsi > 70 and macd < signal_macd:
            messages.append("⚠️ Attention : RSI élevé et MACD baissier. Cela peut annoncer une correction à venir.")
            score -= 2

    # Score final
    if score >= 3:
        messages.append("🔥 Analyse très favorable. Les signaux sont globalement haussiers.")
    elif score <= -3:
        messages.append("🚨 Analyse défavorable. Les indicateurs suggèrent un risque élevé.")
    else:
        messages.append("⚠️ Tendance incertaine. Les signaux sont mixtes ou peu marqués.")

    return "\n\n".join(messages)
