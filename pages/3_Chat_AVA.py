
import streamlit as st
import requests
from datetime import datetime
import pytz
from newsapi import NewsApiClient
import os
import pandas as pd

# --- Clés API ---
API_KEY_METEO = "26b32c230513505762cb096f4d05b0cc"
API_KEY_NEWS = "681120bace124ee99d390cc059e6aca5"

# --- Initialisation ---
newsapi = NewsApiClient(api_key=API_KEY_NEWS)

# --- Fonction météo ---
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
            return f"❌ Météo non disponible pour {ville} (Code : {data.get('cod')} - {data.get('message')})"
    except Exception as e:
        return f"❌ Erreur réseau lors de la récupération de la météo : {e}"

# --- Fonction actus ---
def get_general_news():
    try:
        headlines = newsapi.get_top_headlines(language="en", country="us", page_size=3)
        articles = headlines.get("articles", [])
        if articles:
            return "\n\n".join([f"🔹 [{a['title']}]({a['url']})" for a in articles])
        else:
            return "❌ Aucune actualité disponible."
    except Exception as e:
        return f"❌ Erreur actu : {e}"

# --- Configuration de la page ---
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# --- Initialisation de l'historique ---
if "historique" not in st.session_state:
    st.session_state.historique = []

# --- Sélecteur de ticker (pour réponses adaptées) ---
ticker = st.selectbox("📌 Choisissez un actif :", ["AAPL", "TSLA", "BTC", "ETH"])

# --- Saisie de la ville pour la météo ---
ville_meteo = st.text_input("🏙️ Entrez votre ville pour la météo (optionnel)", "Paris")

# --- Champ d'entrée utilisateur ---
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

ville_meteo = st.text_input("🏙️ Entrez une ville pour la météo :", "Paris", key="ville_input")

# --- Traitement du message ---
if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    # --- Actualités ---
    if "actualité" in question or "news" in question:
        message_bot = f"📰 Voici les actualités :\n\n{get_general_news()}"

    # --- Météo ---
    elif "météo" in question or "quel temps" in question:
        ville_detectee = "Paris"
        for mot in question.split():
            if mot[0].isupper() and len(mot) > 2:
                ville_detectee = mot
        message_bot = get_meteo_ville(ville_detectee)

    # --- Salutation ---
    elif "salut" in question or "bonjour" in question:
        message_bot = f"👋 Hello ! Je suis AVA. Besoin d’un conseil sur {ticker} ?"

    # --- Analyse automatique si le message parle d'un ticker connu ---
    elif any(symb in question for symb in ["aapl", "tsla", "googl", "btc", "eth"]):
        from utils.analyse_technique import analyse_signaux

        nom_ticker = question.replace(" ", "").replace("-", "")
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

        data_path = f"data/donnees_{nom_ticker}.csv"

        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            message_bot = f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n" + analyse_signaux(df)
        else:
            message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}. Lancez le script d'entraînement avant."

    # --- Réponse par défaut ---
    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    # --- Historique ---
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# --- Affichage historique ---
for auteur, message in st.session_state.historique:
    role = "user" if "🧑‍💻" in auteur else "assistant"
    with st.chat_message(role):
        st.markdown(message)
