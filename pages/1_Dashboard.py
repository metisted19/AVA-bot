import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

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

# --- Interface Streamlit ---
st.set_page_config(page_title="Dashboard AVA", layout="wide")
st.title("📊 Dashboard AVA")
st.markdown("Bienvenue sur le tableau de bord interactif d’AVA !")

# --- Sélection du ticker ---
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("Choisissez un actif :", tickers)

# --- Chemin des données ---
data_path = f"data/donnees_{ticker.lower()}.csv"

# --- Affichage des données ---
if os.path.exists(data_path):
    df = charger_donnees(data_path)
    st.subheader(f"Vue d'ensemble - {ticker}")
    st.dataframe(df.tail(10), use_container_width=True)

    # --- Candlestick Chart ---
    st.subheader("📈 Graphique en bougies japonaises avec SMA/EMA")
    fig = go.Figure()
# --- Prédictions IA ---
st.subheader("🤖 Prédiction de l'IA vs Réalité")

# Chargement des prédictions
prediction_path = f"predictions/prediction_{ticker.lower()}.txt"
if os.path.exists(prediction_path):
    try:
        df_pred = pd.read_csv(prediction_path)

        if "prediction" in df_pred.columns:
            df["prediction"] = df_pred["prediction"].values[-len(df):]  # Associer à la fin du DataFrame existant

            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines", name="Prix réel"))
            fig_pred.add_trace(go.Scatter(x=df["date"], y=df["prediction"], mode="lines", name="Prédiction IA"))
            fig_pred.update_layout(
                xaxis_title="Date",
                yaxis_title="Prix",
                height=400
            )
            st.plotly_chart(fig_pred, use_container_width=True)
        else:
            st.warning("❌ Le fichier de prédictions ne contient pas de colonne 'prediction'.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des prédictions : {e}")
else:
    st.info("ℹ️ Aucune prédiction disponible pour cet actif. Lancez le script d'entraînement pour générer les prédictions.")

    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='Bougies'
    ))

    if "sma_10" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["sma_10"], mode='lines', name='SMA 10'))

    if "ema_10" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ema_10"], mode='lines', name='EMA 10'))

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Prix',
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- RSI Chart ---
    if "rsi" in df.columns:
        st.subheader("📉 Indicateur RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df['date'], y=df['rsi'], mode='lines', name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
        fig_rsi.update_layout(height=300, xaxis_title="Date", yaxis_title="RSI")
        st.plotly_chart(fig_rsi, use_container_width=True)
else:
    st.error(f"❌ Aucune donnée trouvée pour {ticker}. Veuillez lancer le script d'entraînement.")
import feedparser

st.subheader("📰 Actualités financières récentes")

# Exemple de flux RSS fiable (Investing)
flux_rss = "https://www.investing.com/rss/news_301.rss"
flux = feedparser.parse(flux_rss)

if flux.entries:
    for entry in flux.entries[:5]:
        st.markdown(f"🔹 [{entry.title}]({entry.link})", unsafe_allow_html=True)
else:
    st.info("Aucune actualité n’a pu être récupérée pour le moment.")






