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

# --- Candlestick Chart avec SMA et EMA ---
st.subheader("📈 Graphique en bougies japonaises avec SMA/EMA")

fig = go.Figure()

# Bougies japonaises
fig.add_trace(go.Candlestick(
    x=df["date"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Bougies"
))

# SMA 10
if "sma_10" in df.columns:
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["sma_10"],
        mode="lines",
        line=dict(width=1.5, dash='dot'),
        name="SMA 10"
    ))

# EMA 10
if "ema_10" in df.columns:
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["ema_10"],
        mode="lines",
        line=dict(width=1.5),
        name="EMA 10"
    ))

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Prix",
    xaxis_rangeslider_visible=False,
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
# --- Zone dédiée au RSI ---
st.subheader("📉 RSI (Relative Strength Index)")
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(
    x=df["date"],
    y=df["rsi"],
    mode='lines',
    name='RSI',
    line=dict(color='blue')
))
# Ajouter les lignes de seuils 30 et 70
fig_rsi.add_shape(type="line", x0=df["date"].min(), x1=df["date"].max(), y0=70, y1=70,
                  line=dict(color="red", dash="dash"), name='Seuil 70')
fig_rsi.add_shape(type="line", x0=df["date"].min(), x1=df["date"].max(), y0=30, y1=30,
                  line=dict(color="green", dash="dash"), name='Seuil 30')
fig_rsi.update_layout(
    yaxis_title="RSI",
    height=300
)
st.plotly_chart(fig_rsi, use_container_width=True)

    
# --- Graphique RSI ---
if "rsi" in df.columns:
    st.subheader("📉 Indicateur RSI (14)")

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df["date"],
        y=df["rsi"],
        mode="lines",
        name="RSI",
        line=dict(color="blue")
    ))

    # Zones de surachat (>70) et survente (<30)
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")

    fig_rsi.update_layout(
        height=300,
        xaxis_title="Date",
        yaxis_title="RSI",
        yaxis_range=[0, 100],
        showlegend=True
    )

    st.plotly_chart(fig_rsi, use_container_width=True)
  

    # --- RSI Line Chart ---
    if "rsi" in df.columns:
        st.subheader("📉 Indicateur RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=df["date"],
            y=df["rsi"],
            mode='lines',
            name='RSI',
            line=dict(color='blue')
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Suracheté", annotation_position="top right")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Survendu", annotation_position="bottom right")
        fig_rsi.update_layout(
            xaxis_title='Date',
            yaxis_title='RSI',
            height=300
        )
        st.plotly_chart(fig_rsi, use_container_width=True)

    else:
        st.warning("L'indicateur RSI n'est pas disponible pour cet actif.")
else:
    st.error(f"Aucune donnée trouvée pour {ticker}. Veuillez lancer le script d'entraînement.")




