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
            messages.append("📈 Le MACD vient de croiser au-dessus de sa ligne de signal. Un regain d'élan haussier est possible.")
        elif macd < signal_macd:
            messages.append("📉 Le MACD est passé sous sa ligne de signal. Un essoufflement de la tendance pourrait se profiler.")

    if rsi is not None:
        if rsi < 30:
            messages.append("🟢 Le RSI est en dessous de 30. L'actif semble survendu, un rebond pourrait survenir. Restez attentif.")
        elif rsi > 70:
            messages.append("🔴 Le RSI dépasse 70. Prudence, nous sommes peut-être en zone de surachat.")

    if close is not None and bb_lower is not None:
        if close < bb_lower:
            messages.append("📉 Le cours a franchi la bande inférieure de Bollinger. Cela pourrait signaler une opportunité à la hausse, si confirmé par d'autres indicateurs.")

    if adx is not None:
        if adx > 25:
            messages.append("💪 L'ADX est au-dessus de 25. Cela renforce l’idée d’une tendance bien installée.")
        elif adx < 20:
            messages.append("😴 L'ADX est faible. Le marché est probablement en consolidation, sans direction forte.")

    if cci is not None:
        if cci > 100:
            messages.append("📈 Le CCI indique une zone de surachat. Peut-être un excès d’enthousiasme ?")
        elif cci < -100:
            messages.append("📉 Le CCI montre une zone de survente. Un retournement haussier pourrait s’esquisser.")

    if williams_r is not None:
        if williams_r < -80:
            messages.append("🟢 Williams %R < -80. L’actif est profondément survendu.")
        elif williams_r > -20:
            messages.append("🔴 Williams %R > -20. L’actif est suracheté, vigilance.")

    # Analyse combinée renforcée
    if rsi is not None and macd is not None and signal_macd is not None:
        if rsi < 30 and macd > signal_macd:
            messages.append("🚀 Un signal puissant ! Le RSI bas combiné à un MACD haussier pourrait indiquer un excellent point d'entrée.")
        elif rsi > 70 and macd < signal_macd:
            messages.append("⚠️ Attention : RSI élevé et MACD baissier. Cela peut annoncer une correction à venir.")

    if not messages:
        return "🤔 Aucun signal clair détecté pour le moment. Restez concentré, les opportunités ne tarderont pas à se manifester."

    return "\n\n".join(messages)








