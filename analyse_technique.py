import pandas as pd
import ta

def ajouter_indicateurs_techniques(df):
    df = df.copy()

    if 'Date' in df.columns:
        df = df.rename(columns={'Date': 'date'})

    df['sma'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['ema'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
    df['macd'] = ta.trend.macd_diff(df['Close'])
    df['adx'] = ta.trend.adx(df['High'], df['Low'], df['Close'])
    df['cci'] = ta.trend.cci(df['High'], df['Low'], df['Close'], window=20)
    df['willr'] = ta.momentum.williams_r(df['High'], df['Low'], df['Close'], lbp=14)

    return df

def analyser_signaux_techniques(df):
    signaux = []

    if 'rsi' in df.columns and not df['rsi'].isna().all():
        rsi = df['rsi'].iloc[-1]
        if rsi < 30:
            signaux.append("🔽 RSI indique une **sous-évaluation** possible (RSI < 30)")
        elif rsi > 70:
            signaux.append("🔼 RSI indique une **surchauffe** potentielle (RSI > 70)")

    if 'macd' in df.columns and not df['macd'].isna().all():
        macd = df['macd'].iloc[-1]
        if macd > 0:
            signaux.append("📈 MACD est **positif**, ce qui indique une tendance haussière")
        else:
            signaux.append("📉 MACD est **négatif**, ce qui peut signaler une baisse")

    if 'adx' in df.columns and df['adx'].iloc[-1] > 25:
        signaux.append("💪 ADX indique une **tendance forte** (ADX > 25)")

    if 'cci' in df.columns:
        cci = df['cci'].iloc[-1]
        if cci > 100:
            signaux.append("📊 CCI suggère une situation de **surachat** (CCI > 100)")
        elif cci < -100:
            signaux.append("📉 CCI suggère une situation de **survente** (CCI < -100)")

    if 'willr' in df.columns:
        willr = df['willr'].iloc[-1]
        if willr < -80:
            signaux.append("📉 Williams %R indique un **survente**")
        elif willr > -20:
            signaux.append("📈 Williams %R indique un **surachat**")

    suggestion = "Aucune action claire recommandée pour le moment."
    if "sous-évaluation" in " ".join(signaux).lower():
        suggestion = "💡 Peut-être une **opportunité d'achat**."
    elif "surchauffe" in " ".join(signaux).lower():
        suggestion = "⚠️ Attention, peut être une zone de **prise de bénéfices**."

    analyse = "\n".join(signaux) if signaux else "Aucun signal technique détecté."
    return analyse, suggestion
