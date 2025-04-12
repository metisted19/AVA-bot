import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Sélection du ticker ---
tickers_disponibles = ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "GOOGL", "^FCHI"]
ticker = st.selectbox("Sélectionnez un actif à analyser :", tickers_disponibles)

# --- Chargement des données ---
data_path = f"data/donnees_{ticker.lower().replace('-', '').replace('^', '')}.csv"
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
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

        st.subheader(f"Analyse technique pour {ticker.upper()}")
        st.markdown(f"{analyse}")
        st.markdown(f"\n💡 **Résumé d'AVA :**\n{resume}")
        st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

    except Exception as e:
        st.error(f"Une erreur est survenue pendant l'analyse : {e}")
else:
    st.warning(f"Aucune donnée trouvée pour {ticker}. Veuillez lancer l'entraînement AVA.")









