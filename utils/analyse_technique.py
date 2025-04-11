def analyser_signaux_techniques(data):
    analyse = []
    suggestion = ""

    try:
        rsi = data['RSI'].iloc[-1]
        macd = data['MACD'].iloc[-1]
        macd_signal = data['MACD_signal'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]

        # Analyse technique brute
        if rsi > 70:
            analyse.append("RSI élevé : le marché pourrait être en situation de surachat.")
        elif rsi < 30:
            analyse.append("RSI faible : possible situation de survente.")

        if macd > macd_signal:
            analyse.append("MACD au-dessus du signal : dynamique haussière.")
        else:
            analyse.append("MACD en dessous du signal : pression vendeuse.")

        if ema_20 > sma_50:
            analyse.append("EMA 20 au-dessus de la SMA 50 : tendance haussière à court terme.")
        else:
            analyse.append("EMA 20 en dessous de la SMA 50 : tendance baissière à surveiller.")

        # Génération de la suggestion vivante
        if rsi < 30 and macd < macd_signal:
            suggestion = "C’est calme plat… trop calme. Le marché semble survendu, mais la tendance reste incertaine. Je garderais un œil attentif sans me précipiter."
        elif macd > macd_signal and rsi < 70:
            suggestion = "Des signaux haussiers apparaissent ! Si j’avais un portefeuille, j’irais peut-être gratter une opportunité d’achat discrète…"
        elif rsi > 70 and macd < macd_signal:
            suggestion = "Attention, surachat + perte de vitesse... Ça sent le piège des acheteurs trop confiants. Une pause s’impose."
        else:
            suggestion = "Analyse mitigée. Je reste prudente et j’observe encore un peu… Patience, c’est aussi une stratégie !"

    except Exception as e:
        analyse.append("Impossible d'analyser les données : " + str(e))
        suggestion = "Je ne peux pas vous guider sans données fiables. Essayez de recharger l’actif."

    return "\n".join(analyse), suggestion

