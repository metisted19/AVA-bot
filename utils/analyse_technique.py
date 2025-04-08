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
            messages.append("📈 Le MACD vient de croiser au-dessus de sa ligne de signal. C'est souvent bon signe, ça sent la reprise ! 💪")
        elif macd < signal_macd:
            messages.append("📉 Le MACD est passé sous sa ligne de signal. Reste vigilant, ça peut glisser. 🧊")

    if rsi is not None:
        if rsi < 30:
            messages.append("🟢 RSI < 30 → l'actif semble survendu. Une belle occasion à surveiller de près ? 👀")
        elif rsi > 70:
            messages.append("🔴 RSI > 70 → attention, on entre en zone de surachat. Ne fonce pas tête baissée ! 🚧")

    if close is not None and bb_lower is not None:
        if close < bb_lower:
            messages.append("📉 Le cours a touché la bande inférieure de Bollinger. Peut-être le calme avant le rebond ? 🌀")

    if adx is not None:
        if adx > 25:
            messages.append("💪 ADX > 25 → la tendance est solide, comme un roc. 🚀")
        elif adx < 20:
            messages.append("😴 ADX < 20 → marché endormi… Pas beaucoup d'élan pour le moment. 💤")

    if cci is not None:
        if cci > 100:
            messages.append("📈 CCI > 100 → actif peut-être suracheté. C’est chaud, mais attention à la surchauffe 🔥")
        elif cci < -100:
            messages.append("📉 CCI < -100 → actif survendu. Une opportunité qui couve ? 👀")

    if williams_r is not None:
        if williams_r < -80:
            messages.append("🟢 Williams %R < -80 → zone de survendu. Potentiel de rebond ?")
        elif williams_r > -20:
            messages.append("🔴 Williams %R > -20 → zone de surachat. Prudence si tu es déjà positionné.")

    # Analyse combinée renforcée
    if rsi is not None and macd is not None and signal_macd is not None:
        if rsi < 30 and macd > signal_macd:
            messages.append("🚀 RSI bas + MACD haussier = Signal d'achat fort détecté ! C’est peut-être le moment d’entrer en piste ! 🎯")
        elif rsi > 70 and macd < signal_macd:
            messages.append("⚠️ RSI élevé + MACD baissier = Attention au retournement baissier. Un repli semble se préparer. 🕳️")

    if not messages:
        return "🤔 Pour l’instant, je ne détecte aucun signal clair. Mais t’inquiète, je garde un œil sur les marchés pour toi ! 👁️📉"

    return "\n\n".join(messages)





