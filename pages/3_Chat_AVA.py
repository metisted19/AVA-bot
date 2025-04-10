import streamlit as st
import requests
from datetime import datetime
import pytz

# --- Clés API ---
API_KEY_METEO = "ta_nouvelle_cle_obtenue"  # Remplace par la vraie clé
API_KEY_NEWS = "ta_cle_newsapi"  # Remplace par ta vraie clé

# --- Fonction pour la météo ---
def get_meteo_ville(ville):
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Paris&appid=ta_nouvelle_cle_obtenue&units=metric&lang=fr"

    try:
        response = requests.get(url)
        data = response.json()
        
        # Afficher la réponse brute pour débogage
        print(data)  # Ajoute ceci pour voir la réponse brute

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
    url = f"https://newsapi.org/v2/top-headlines?country=fr&apiKey={API_KEY_NEWS}"
    try:
        response = requests.get(url)
        data = response.json()

        # Afficher la réponse brute pour débogage
        print(data)  # Ajoute ceci pour voir la réponse brute

        if data["status"] == "ok" and data["totalResults"] > 0:
            news = []
            for article in data["articles"][:5]:
                titre = article.get("title", "Sans titre")
                lien = article.get("url", "#")
                news.append(f"🔹 [{titre}]({lien})")
            return "\n\n".join(news)
        else:
            return "❌ Impossible de récupérer les actualités du jour."
    except Exception as e:
        return f"❌ Erreur lors de la récupération des actualités : {e}"

# Configuration de la page
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# Zone d'historique du chat
if "historique" not in st.session_state:
    st.session_state.historique = []

# Champ de saisie utilisateur
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

# Traitement du message
if user_input:
    question = user_input.lower().strip()  # Normaliser la question de l'utilisateur
    message_bot = ""  # Initialiser la réponse du bot

    # Vérification des conditions d'entrée de l'utilisateur pour répondre avec les actualités
    if "actualités du jour" in question or "news" in question:
        message_bot = f"📰 Voici les actualités générales du jour :\n\n{get_general_news()}"
    
    # Vérification des conditions d'entrée de l'utilisateur pour la météo
    elif "météo" in question or "quel temps" in question or "temps" in question:
        ville = "Paris"  # Ville par défaut, tu pourrais demander à l'utilisateur d'entrer une ville
        meteo = get_meteo_ville(ville)
        message_bot = meteo

    else:
        # Si la question ne correspond à rien de spécifique, on renvoie un message par défaut
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    # Ajout à l'historique des messages
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# Affichage de l'historique
if st.session_state.historique:
    for auteur, message in st.session_state.historique:
        with st.chat_message(auteur):
            st.markdown(message)


