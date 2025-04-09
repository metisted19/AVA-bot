import streamlit as st
import pandas as pd
import datetime
import pytz
import os

# Configuration de la page
st.set_page_config(page_title="📊 Signaux & Alertes", layout="wide")
st.title("📡 Détection de signaux et alertes AVA")

# Chargement des données
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

# Sélection d’actif
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("📌 Choisissez un actif :", tickers)
data_path = f"data/donnees_{ticker.lower()}.csv"

# --- Section Signaux ---

st.title("📊 Signaux d'Analyse et Prédictions")

# Sélectionner un actif
ticker = st.selectbox("📌 Choisissez un actif :", tickers)

# Lire les données de prédiction
prediction_path = f"predictions/prediction_{ticker.lower()}.csv"

# Lire et afficher les prédictions
if os.path.exists(prediction_path):
    prediction_df = pd.read_csv(prediction_path)
    last_prediction = prediction_df["prediction"].iloc[-1]

    # Afficher la prédiction dans Signaux
    st.subheader(f"Prédiction de l'IA pour {ticker} :")
    if last_prediction == 1:
        st.markdown("📈 Hausse prévue pour demain")
    else:
        st.markdown("📉 Baisse prévue pour demain")
else:
    st.warning(f"❌ Aucun fichier de prédiction trouvé pour {ticker}.")

# Affichage des autres signaux comme RSI, etc.
st.subheader(f"Indicateur RSI pour {ticker} :")
# Ajoutez ici votre code pour afficher le RSI et autres signaux

# Si le fichier existe
if os.path.exists(data_path):
    df = charger_donnees(data_path)
    df = df.sort_values("date")

    st.subheader(f"🔍 Analyse des signaux techniques pour {ticker}")

    alertes = []

    # 🔼 Hausse ou 🔽 Baisse sur 3 jours consécutifs
    df['delta_close'] = df['close'].diff()
    df['direction'] = df['delta_close'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    df['streak'] = df['direction'].groupby((df['direction'] != df['direction'].shift()).cumsum()).transform('size') * df['direction']
    if df['streak'].iloc[-1] >= 3:
        alertes.append("🔼 **Hausse sur 3 jours consécutifs** détectée !")
    elif df['streak'].iloc[-1] <= -3:
        alertes.append("🔽 **Baisse sur 3 jours consécutifs** détectée !")

    # 💥 Croisement SMA/EMA
    if 'sma_10' in df.columns and 'ema_10' in df.columns:
        if df['sma_10'].iloc[-2] < df['ema_10'].iloc[-2] and df['sma_10'].iloc[-1] > df['ema_10'].iloc[-1]:
            alertes.append("💥 **Croisement haussier SMA/EMA** détecté !")
        elif df['sma_10'].iloc[-2] > df['ema_10'].iloc[-2] and df['sma_10'].iloc[-1] < df['ema_10'].iloc[-1]:
            alertes.append("💥 **Croisement baissier SMA/EMA** détecté !")

    # 🔄 RSI extrême
    if 'rsi' in df.columns:
        if df['rsi'].iloc[-1] > 70:
            alertes.append("🔴 **RSI > 70 : Surachat** !")
        elif df['rsi'].iloc[-1] < 30:
            alertes.append("🟢 **RSI < 30 : Survente** !")

    # 📉 Croisement MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
            alertes.append("📈 **Croisement haussier MACD** détecté !")
        elif df['macd'].iloc[-2] > df['macd_signal'].iloc[-2] and df['macd'].iloc[-1] < df['macd_signal'].iloc[-1]:
            alertes.append("📉 **Croisement baissier MACD** détecté !")

    # ⚠️ Tendance forte détectée (ADX > 25)
    if 'adx' in df.columns:
        if df['adx'].iloc[-1] > 25:
            alertes.append("⚠️ **Tendance forte en cours (ADX > 25)**")

    # Affichage des alertes
    if alertes:
        for alerte in alertes:
            st.success(alerte)
    else:
        st.info("Aucune alerte technique majeure détectée aujourd'hui.")

    # Affichage des dernières lignes
    st.subheader("📄 Données récentes")
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.error(f"❌ Aucune donnée trouvée pour {ticker}. Veuillez lancer le script d'entraînement.")








