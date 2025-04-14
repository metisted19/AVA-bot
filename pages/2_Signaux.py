import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers disponibles et noms à afficher ---
tickers_disponibles = [
    "aapl", "tsla", "googl", "btc-usd", "eth-usd",
    "msft", "amzn", "nvda", "^gspc","doge-usd", "ada-usd"
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
    "ada-usd": "Cardano"
}

# --- Sélection du ticker ---
ticker = st.selectbox("Choisissez un actif :", options=tickers_disponibles, format_func=lambda x: nom_affichages[x])

# --- Chargement des données ---
fichier_data = f"data/donnees_{ticker.lower()}.csv"
fichier_pred = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^', '')}.csv"

if os.path.exists(fichier_data):
    df = pd.read_csv(fichier_data)
    df.columns = [col.capitalize() for col in df.columns]
    df = ajouter_indicateurs_techniques(df)

    try:
        # --- Analyse technique ---
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

        # --- Affichage complet ---
        st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
        st.markdown(analyse)
        st.markdown(f"💬 **Résumé d'AVA :**\n{resume}")
        st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

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











