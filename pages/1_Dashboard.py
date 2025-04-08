import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from utils.analyse_technique import analyse_signaux  # ✅ Analyse technique d’AVA

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

# Interface Streamlit
st.set_page_config(page_title="📈 Signaux AVA", layout="wide")
st.title("📈 Signaux détectés")
st.markdown("Voici les signaux d’achat/vente détectés par AVA sur les indicateurs techniques.")

# Sélection de l'actif
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("Choisissez un actif :", tickers)

data_path = f"data/donnees_{ticker.lower()}.csv"

if os.path.exists(data_path):
    df = charger_donnees(data_path)

    st.subheader(f"📊 Données récentes pour {ticker}")
    colonnes_affichage = ['date', 'close', 'macd', 'macd_signal', 'rsi', 'bb_lower', 'adx', 'cci', 'williams_r']
    colonnes_disponibles = [col for col in colonnes_affichage if col in df.columns]

    try:
        signaux = ['Signal_MACD', 'Signal_RSI', 'Signal_BB', 'Signal_ADX', 'Signal_CCI', 'Signal_WR']
        colonnes_signaux = [s for s in signaux if s in df.columns]
        st.dataframe(df[colonnes_disponibles + colonnes_signaux].tail(10), use_container_width=True)
    except:
        st.dataframe(df[colonnes_disponibles].tail(10), use_container_width=True)

    # Graphique en bougies
    st.subheader("📈 Graphique en bougies japonaises")
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

    # Analyse technique d'AVA
    st.subheader("🔎 Analyse d’AVA")
    interpretation = analyse_signaux(df)
    st.markdown(interpretation)

else:
    st.error(f"❌ Colonne 'date' manquante ou données indisponibles pour {ticker}.")





