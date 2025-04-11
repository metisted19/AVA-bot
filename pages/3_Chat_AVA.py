import streamlit as st
import os
import sys
import pandas as pd

# Modules locaux
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites
from fonctions_meteo import obtenir_meteo

# Chemin pour import local si le script est lancé depuis /pages/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("🤖 AVA - Chat IA")
st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités...")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Fonction sentiment
def analyser_sentiment(news_list):
    mots_positifs = ["progress", "gain", "rise", "success", "growth"]
    mots_negatifs = ["fall", "loss", "drop", "crash", "recession"]
    score = 0
    for titre, _ in news_list:
        titre = titre.lower()
        score += sum(1 for mot in mots_positifs if mot in titre)
        score -= sum(1 for mot in mots_negatifs if mot in titre)
    if score > 1:
        return "🟢 Le sentiment global du marché est **positif**."
    elif score < -1:
        return "🔴 Le sentiment global du marché est **négatif**."
    else:
        return "🟡 Le sentiment global du marché est **neutre**."

# Affichage des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur
question = st.chat_input("Une question pour AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        question_clean = question.lower().strip()
        message_bot = ""

        if "actu" in question_clean or "news" in question_clean:
            actualites = obtenir_actualites()
            sentiment = analyser_sentiment(actualites)
            message_bot = "🗞️ Voici les dernières actualités :\n\n"
            for titre, url in actualites:
                message_bot += f"- [{titre}]({url})\n"
            message_bot += f"\n{sentiment}"

        elif "météo" in question_clean:
            ville = "Paris"
            for mot in question.split():
                if mot.istitle():
                    ville = mot
            message_bot = obtenir_meteo(ville)

        elif any(symb in question_clean for symb in ["aapl", "tsla", "googl", "btc", "eth", "fchi", "cac"]):
            nom_ticker = question_clean.replace(" ", "").replace("-", "")
            if "btc" in nom_ticker:
                nom_ticker = "btc-usd"
            elif "eth" in nom_ticker:
                nom_ticker = "eth-usd"
            elif "aapl" in nom_ticker:
                nom_ticker = "aapl"
            elif "tsla" in nom_ticker:
                nom_ticker = "tsla"
            elif "googl" in nom_ticker:
                nom_ticker = "googl"
            elif "fchi" in nom_ticker or "cac" in nom_ticker:
                nom_ticker = "^fchi"

            data_path = f"data/donnees_{nom_ticker}.csv"
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                df = ajouter_indicateurs_techniques(df)
                try:
                    analyse, suggestion = analyser_signaux_techniques(df)
                    message_bot = (
                        f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n"
                        f"{analyse}\n\n"
                        f"🤖 *Mon intuition d'IA ?* {suggestion}"
                    )
                except Exception as e:
                    message_bot = f"⚠️ Une erreur est survenue pendant l'analyse : {e}"
            else:
                message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}.
Lancez le script d'entraînement."

        else:
            message_bot = obtenir_reponse_ava(question)

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})
# Reset
st.sidebar.button("🧹 Effacer l'historique", on_click=lambda: st.session_state.clear())
