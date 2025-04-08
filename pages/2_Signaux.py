import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Fonction pour charger les données ---
@st.cache_data
def charger_donnees(path):
    df = pd.read_csv(path)
    if 'date' not in df.columns:
        df.reset_index(inplace=True)
    if 'Date' in df.columns and 'date' not in df.columns:
        df.rename(columns={'Date': 'date'}, inplace=True)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
    return df

# --- Fonction d'analyse des signaux techniques ---
def analyse_signaux(df):
    messages = []

    # RSI
    if 'rsi' in df.columns:
        rsi = df['rsi'].iloc[-1]
        if rsi > 70:
            messages.append("🔴 RSI élevé : possible surachat. Prudence, un retournement est possible.")
        elif rsi < 30:
            messages.append("🟢 RSI bas : actif potentiellement survendu. Cela peut annoncer une hausse.")

    # MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        macd = df['macd'].iloc[-1]
        signal = df['macd_signal'].iloc[-1]
        if macd > signal:
            messages.append("📈 MACD haussier : le momentum semble positif.")
        elif macd < signal:
            messages.append("📉 MACD baissier : le momentum est en perte de vitesse.")

    # Bollinger
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

# --- Interface Chatbot ---
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Chat avec AVA")
st.markdown("Pose ta question à AVA ou demande une analyse !")

# Sélection de l’actif à analyser
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("Choisis un actif pour l’analyse d’AVA :", tickers)
data_path = f"data/donnees_{ticker.lower()}.csv"

# Chargement et analyse
if os.path.exists(data_path):
    df = charger_donnees(data_path)
    ava_response = analyse_signaux(df)
else:
    ava_response = "❌ Données introuvables pour cet actif. Veuillez les générer d’abord."

# Champ de discussion
user_input = st.text_input("Vous :", "")
if user_input:
    st.markdown(f"**Vous :** {user_input}")
    st.markdown("**AVA :**")

    # Analyse automatique si l'utilisateur demande une analyse
    if any(mot in user_input.lower() for mot in ["analyse", "avis", "qu'en penses-tu", "analyse technique"]):
        st.success(ava_response)
    else:
        # Réponses classiques
        reponses_generiques = [
            "Je suis là pour t’aider à décoder les signaux du marché. Tu veux une analyse ?",
            "N’oublie pas : la patience est souvent la meilleure stratégie.",
            "Je peux te donner une analyse technique si tu veux 😉",
        ]
        st.info(reponses_generiques[len(user_input) % len(reponses_generiques)])

else:
    st.caption("💡 Essaie : 'Peux-tu me faire une analyse technique sur cet actif ?'")



