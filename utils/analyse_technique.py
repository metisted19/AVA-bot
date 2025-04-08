def analyse_signaux(df):
    messages = []

    # Analyse RSI
    if 'rsi' in df.columns:
        rsi = df['rsi'].iloc[-1]
        if rsi > 70:
            messages.append("🔴 RSI élevé : possible surachat. Prudence, un retournement est possible.")
        elif rsi < 30:
            messages.append("🟢 RSI bas : actif potentiellement survendu. Cela peut annoncer une hausse.")

    # Analyse MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        macd = df['macd'].iloc[-1]
        signal = df['macd_signal'].iloc[-1]
        if macd > signal:
            messages.append("📈 MACD haussier : le momentum semble positif.")
        elif macd < signal:
            messages.append("📉 MACD baissier : le momentum est en perte de vitesse.")

    # Analyse des bandes de Bollinger
    if 'close' in df.columns and 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        close = df['close'].iloc[-1]
        upper = df['bb_upper'].iloc[-1]
        lower = df['bb_lower'].iloc[-1]
        if close > upper:
            messages.append("🚨 Le cours a dépassé la bande supérieure de Bollinger. Cela peut indiquer une surévaluation.")
        elif close < lower:
            messages.append("📉 Le cours est sous la bande inférieure de Bollinger. Rebond possible ?")

    if not messages:
        return "🤖 Aucun signal significatif détecté pour le moment. Reste en veille..."
    else:
        return "\n".join(messages)
