
import streamlit as st
import requests
from datetime import datetime
import pytz
from newsapi import NewsApiClient

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

if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    if "actualité" in question or "news" in question:
        message_bot = f"📰 Voici les actualités :\n\n{get_general_news()}"

    elif "météo" in question or "quel temps" in question or "temps" in question:
        message_bot = get_meteo_ville(ville_meteo)

    elif "salut" in question or "bonjour" in question:
        message_bot = f"Hello ! Ici AVA. {ticker} vous intéresse aujourd'hui ? Prête à analyser tout cela 💼"

    elif "btc" in question or ticker == "BTC-USD":
        message_bot = "🚀 Bitcoin est souvent imprévisible... mais j'aime ça. Vous voulez une analyse technique ?"

    elif ticker == "TSLA":
        message_bot = "⚡ Tesla vibre entre innovation et volatilité. Une analyse technique vous tente ?"

    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    # ✅ Ce bloc fait bien partie du `if user_input:` donc il est bien indenté
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# --- Affichage historique ---
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)
