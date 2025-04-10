import streamlit as st
import requests
from datetime import datetime
import pytz
from newsapi import NewsApiClient

# --- CLÉS API ---
API_KEY_METEO = "681120bace124ee99d390cc059e6aca5"  # Remplace par ta vraie clé
API_KEY_NEWS = "681120bace124ee99d390cc059e6aca5"  # Clé NewsAPI

# --- Initialisation client NewsAPI ---
newsapi = NewsApiClient(api_key=API_KEY_NEWS)

# --- Fonction Météo ---
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
        return f"❌ Erreur lors de la récupération météo : {e}"

# --- Fonction Actualités ---
def get_general_news():
    try:
        top_headlines = newsapi.get_top_headlines(
            language="fr",
            country="fr",
            page_size=5
        )
        articles = top_headlines["articles"]
        if articles:
            news = []
            for article in articles:
                titre = article.get("title", "Sans titre")
                lien = article.get("url", "#")
                news.append(f"🔹 [{titre}]({lien})")
            return "\n\n".join(news)
        else:
            return "❌ Aucune actualité trouvée pour aujourd’hui."
    except Exception as e:
        return f"❌ Erreur lors de la récupération des actualités : {e}"

# --- Configuration de la page ---
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# --- Historique du chat ---
if "historique" not in st.session_state:
    st.session_state.historique = []

# --- Saisie utilisateur ---
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

# --- Traitement du message ---
if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    if "actualité" in question or "news" in question:
        message_bot = f"📰 Voici les actualités générales du jour :\n\n{get_general_news()}"

    elif "météo" in question or "quel temps" in question or "temps" in question:
        ville = "Paris"  # Valeur par défaut
        message_bot = get_meteo_ville(ville)

    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# --- Affichage de l'historique ---
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)
