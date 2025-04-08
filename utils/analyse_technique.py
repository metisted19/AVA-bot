def analyse_signaux(df):
    if df.empty:
        return "⚠️ Je n’ai pas encore assez de données pour donner une analyse fiable."

    dernier = df.iloc[-1]

    messages = []
    rsi = dernier.get("rsi", None)
    macd = dernier.get("macd", None)
    signal = dernier.get("macd_signal", None)
    close = dernier.get("close", None)
    bb_lower = dernier.get("bb_lower", None)
    bb_upper = dernier.get("bb_upper", None)

    # RSI : surachat / survente
    if rsi is not None:
        if rsi > 70:
            messages.append("🔴 RSI élevé : L’actif est en zone de surachat, une correction pourrait arriver.")
        elif rsi < 30:
            messages.append("🟢 RSI faible : L’actif est en zone de survente, un rebond est possible.")
        else:
            messages.append("⚪ RSI neutre : Aucun signal fort actuellement.")

    # MACD croisement
    if macd is not None and signal is not None:
        if macd > signal:
            messages.append("🟢 MACD haussier : Croisement haussier détecté, potentiel d’achat.")
        elif macd < signal:
            messages.append("🔴 MACD baissier : Croisement baissier détecté, prudence.")
        else:
            messages.append("⚪ MACD stable : Pas de croisement significatif.")

    # Bandes de Bollinger
    if close is not None and bb_lower is not None and bb_upper is not None:
        if close < bb_lower:
            messages.append("🟢 Prix sous les bandes de Bollinger : possible retournement haussier.")
        elif close > bb_upper:
            messages.append("🔴 Prix au-dessus des bandes de Bollinger : surachat potentiel.")
        else:
            messages.append("⚪ Prix dans les bandes : situation stable.")

    # Synthèse finale
    if "🟢" in "".join(messages) and "🔴" not in "".join(messages):
        tendance = "✅ Conclusion : les indicateurs montrent une **tendance haussière globale**."
    elif "🔴" in "".join(messages) and "🟢" not in "".join(messages):
        tendance = "⚠️ Conclusion : les signaux indiquent une **tendance baissière à surveiller**."
    else:
        tendance = "🤔 Conclusion : les signaux sont mitigés, restons prudents."

    return "\n\n".join(messages + ["", tendance])



