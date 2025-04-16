import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers disponibles et noms à afficher ---
tickers = [
    "aapl", "tsla", "googl", "btc-usd", "eth-usd",
    "msft", "amzn", "nvda", "^gspc", "doge-usd", "ada-usd",
    "sol-usd", "gc=F", "^fchi", "xrp-usd", "bnb-usd", "cl=F", "si=F",
    "matic-usd", "uni-usd", "^ndx"
]

nom_affichages = {
    "aapl": "Apple",
    "tsla": "Tesla",
    "googl": "Google",
    "btc-usd": "Bitcoin",
    "eth-usd": "Ethereum",
    "msft": "Microsoft",
    "amzn": "Amazon",
    "nvda": "NVIDIA",
    "^gspc": "S&P500",
    "doge-usd": "Dogecoin",
    "ada-usd": "Cardano",
    "^fchi": "CAC 40",
    "sol-usd": "Solana",
    "gc=F": "Or (Gold)",
    "xrp-usd": "XRP",
    "bnb-usd": "BNB",
    "cl=F": "Pétrole brut",
    "si=F": "Argent (Silver)",
    "matic-usd": "Polygon (MATIC)",
    "uni-usd": "Uniswap",
    "^ndx": "Nasdaq 100"
}

# --- Fonction de suggestion d'ouverture de position avec SL/TP ---
def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd = df["Macd"].iloc[-1]
    rsi = df["Rsi"].iloc[-1]
    adx = df["Adx"].iloc[-1]

    if macd > 0 and rsi < 70 and adx > 20:
        position = "📈 Ouverture d’une **position acheteuse** (long)"
        sl = close * 0.97
        tp = close * 1.05
    elif macd < 0 and rsi > 30 and adx > 20:
        position = "📉 Ouverture d’une **position vendeuse** (short)"
        sl = close * 1.03
        tp = close * 0.95
    else:
        return "⚠️ Les conditions ne sont pas assez claires pour une prise de position."

    sl = round(sl, 2)
    tp = round(tp, 2)
    return f"{position}\n\n🛑 Stop-Loss : **{sl}**\n🎯 Take-Profit : **{tp}**"

# --- Sélection du ticker ---
ticker = st.selectbox("Choisissez un actif :", options=tickers, format_func=lambda x: nom_affichages.get(x, x))

# --- Chargement des données ---
fichier_data = f"data/donnees_{ticker.lower()}.csv"
fichier_pred = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^', '').replace('=','')}.csv"

if os.path.exists(fichier_data):
    df = pd.read_csv(fichier_data)
    df.columns = [col.capitalize() for col in df.columns]
    df = ajouter_indicateurs_techniques(df)

    try:
        analyse, suggestion = analyser_signaux_techniques(df)

        def generer_resume_signal(signaux):
            texte = ""
            signaux_str = " ".join(signaux).lower()
            if "survente" in signaux_str:
                texte += "🔻 **Zone de survente détectée.** L'actif pourrait être sous-évalué.\n"
            if "surachat" in signaux_str:
                texte += "🔺 **Zone de surachat détectée.** Attention à une possible correction.\n"
            if "haussier" in signaux_str:
                texte += "📈 **Tendance haussière en cours.** Les indicateurs suggèrent un élan positif.\n"
            if "baissier" in signaux_str:
                texte += "📉 **Tendance baissière détectée.** Prudence sur les mouvements actuels.\n"
            if "faible" in signaux_str:
                texte += "😴 **Manque de tendance.** Le marché semble indécis.\n"
            if texte == "":
                texte = "ℹ️ Aucun signal fort détecté pour l'instant. Restez à l'affût."
            return texte

        signaux_list = analyse.split("\n") if analyse else []
        resume = generer_resume_signal(signaux_list)

        # --- Affichage ---
        st.subheader(f"🔎 Analyse pour {nom_affichages.get(ticker, ticker.upper())}")
        st.markdown(analyse)
        st.markdown(f"💬 **Résumé d'AVA :**\n{resume}")
        st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

        # --- Suggestion de position ---
        st.subheader("📌 Suggestion de position")
        st.markdown(suggerer_position_et_niveaux(df))

        # --- Prédiction IA ---
        if os.path.exists(fichier_pred):
            df_pred = pd.read_csv(fichier_pred)
            prediction = df_pred["prediction"].iloc[-1]
            st.subheader("📈 Prédiction IA (demain) :")
            st.info("📈 Hausse probable demain" if prediction == 1 else "📉 Baisse probable demain")
        else:
            st.warning("Aucune prédiction trouvée.")

        # --- RSI ---
        if 'Rsi' in df.columns:
            st.subheader("📊 RSI actuel :")
            st.metric("RSI", round(df["Rsi"].iloc[-1], 2))

        # --- Données brutes ---
        st.subheader("📄 Données récentes")
        st.dataframe(df.tail(10), use_container_width=True)

    except Exception as e:
        st.error(f"Une erreur est survenue pendant l'analyse : {e}")

else:
    st.warning(f"❌ Aucune donnée trouvée pour {ticker}. Veuillez lancer l'entraînement AVA.")













