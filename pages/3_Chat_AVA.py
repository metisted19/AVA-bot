from datetime import datetime
import pytz
import os
from newsapi import NewsApiClient
from utils.analyse_technique import analyse_signaux
import pandas as pd
import requests
import streamlit as st
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques

# --- Clés API ---
API_KEY_METEO = "26b32c230513505762cb096f4d05b0cc"
API_KEY_NEWS = "681120bace124ee99d390cc059e6aca5"

# --- Initialisation ---
newsapi = NewsApiClient(api_key=API_KEY_NEWS)

# --- Fonction pour la météo ---
def get_meteo_ville(ville):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY_METEO}&units=metric&lang=fr"
    try:
        response = requests.get(url)
        data = response.json()
        if data['cod'] == 200:
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            return f"🌤 Il fait {temp}°C à {ville} avec {description}."
        else:
            code = data.get('cod', '❓')
            msg = data.get('message', 'Erreur inconnue')
            return f"❌ Impossible d'obtenir la météo pour {ville}.\nCode : {code} - Message : {msg}"
    except Exception as e:
        return f"❌ Erreur réseau lors de la récupération météo : {e}"

# --- Fonction pour les actualités ---
def get_general_news():
    try:
        headlines = newsapi.get_top_headlines(language="en", country="us", page_size=5)
        articles = headlines.get("articles", [])
        if articles:
            news_list = []
            for article in articles:
                titre = article.get("title", "Sans titre")
                lien = article.get("url", "#")
                news_list.append((titre, lien))
            return news_list
        else:
            return []
    except Exception as e:
        return []

# --- Fonction d'analyse de sentiment ---
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

# --- Page UI ---
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# --- Historique ---
if "historique" not in st.session_state:
    st.session_state.historique = []

# --- Effacer ---
if st.button("🗑️ Effacer la conversation"):
    st.session_state.historique = []
    st.experimental_rerun()

# --- Saisie utilisateur ---
user_input = st.text_input("🧐 Que souhaitez-vous demander à AVA ?", key="chat_input")

if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    # --- Actualités ---
    if "actualité" in question or "news" in question:
        actus = get_general_news()
        if isinstance(actus, str):
            message_bot = actus
        elif actus:
            message_bot = "📰 Voici les actualités :\n\n" + "\n\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus])
        else:
            message_bot = "❌ Aucune actualité disponible pour le moment."

    # --- Météo ---
    elif "météo" in question or "quel temps" in question:
        ville_detectee = "Paris"
        for mot in question.split():
            if mot[0].isupper() and len(mot) > 2:
                ville_detectee = mot
        message_bot = get_meteo_ville(ville_detectee)

    # --- Réponses simples ---
    elif any(phrase in question for phrase in ["ça va", "comment tu vas", "tu vas bien"]):
        message_bot = "Je vais super bien, prête à analyser le monde avec vous ! Et vous ?"

    elif any(phrase in question for phrase in ["quoi de neuf", "tu fais quoi", "des news"]):
        message_bot = "Je scrute les marchés, je capte les tendances… une journée normale pour une IA boursière !"

    elif any(phrase in question for phrase in ["t'es qui", "tu es qui", "t'es quoi", "tu es quoi"]):
        message_bot = "Je suis AVA, votre assistante virtuelle boursière, météo, et bien plus. Disons... une alliée du futur."

    elif any(phrase in question for phrase in ["tu dors", "t'es là", "tu es là"]):
        message_bot = "Je ne dors jamais. Toujours connectée, toujours prête. Posez votre question !"

    # --- Salutations ---
    elif "salut" in question or "bonjour" in question:
        message_bot = "👋 Bonjour ! Je suis AVA. Besoin d'une analyse ou d'un coup de pouce ? 😊"

    # --- Analyse technique vivante ---
elif any(symb in question.lower() for symb in ["aapl", "tsla", "googl", "btc", "eth", "fchi", "cac"]):
    nom_ticker = question.replace(" ", "").replace("-", "").lower()

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
        message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}.\nLancez le script d'entraînement pour les générer."

    # --- Réponse par défaut ---
    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités, la météo ou une analyse technique ! 😊"
    
    # --- Suppression automatique de l'historique ---
    st.session_state.historique = []

    # --- Ajout dans l'historique ---
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))


# --- Affichage de l'historique ---
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)

