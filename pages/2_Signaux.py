import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from utils.analyse_technique import analyse_signaux

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

# Interface
st.set_page_config(page_title="📈 Signaux AVA", layout="wide")

# Affichage du logo
st.image("ava_logo.png", width=60)

st.title("📈 Signaux détectés")
st.markdown("Voici les signaux d’achat/vente détectés par AVA sur les indicateurs techniques.")

# Choix de l’actif
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("Choisissez un actif :", tickers)

# Chargement des données
data_path = f"data/donnees_{ticker.lower()}.csv"

if os.path.exists(data_path):
    df = charger_donnees(data_path)

    st.subheader(f"📊 Données récentes pour {ticker}")
    colonnes_base = ['date', 'close', 'macd', 'macd_signal', 'rsi', 'bb_lower']
    colonnes_signaux = ['Signal_MACD', 'Signal_RSI', 'Signal_BB']
    colonnes_dispo = [col for col in colonnes_base + colonnes_signaux if col in df.columns]
    st.dataframe(df[colonnes_dispo].tail(10), use_container_width=True)

    # Bougies japonaises + indicateurs
    st.subheader("📈 Graphique en bougies japonaises avec SMA/EMA")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Bougies"
    ))

    if 'sma_10' in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["sma_10"], mode="lines", name="SMA 10"))
    if 'ema_10' in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ema_10"], mode="lines", name="EMA 10"))

    fig.update_layout(xaxis_title="Date", yaxis_title="Prix", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Analyse d'AVA
    st.subheader("🔎 Analyse technique d'AVA")
    interpretation = analyse_signaux(df)
    st.markdown(interpretation)

else:
    st.error("❌ Fichier de données introuvable ou colonne 'date' manquante.")






