import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import pytz
import requests

# Fonction pour récupérer les actualités générales
def get_general_news():
    api_key = "YOUR_API_KEY"  # Remplace par ta clé API NewsAPI
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] == "ok" and data["totalResults"] > 0:
            news = []
            for article in data["articles"][:5]:  # Récupérer les 5 premières actualités
                title = article["title"]
                url = article["url"]
                description = article["description"]
                news.append(f"🔹 [{title}]({url})\n{description}")
            return "\n\n".join(news)
        else:
            return "Désolé, je n'ai pas pu récupérer les actualités. Essayez de nouveau plus tard."
    except Exception as e:
        return f"Erreur lors de la récupération des actualités : {e}"

# Fonction pour récupérer la météo
API_KEY = 'ton_api_key_ici'  # Remplace par ta clé API OpenWeatherMap

def get_meteo_ville(ville):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY}&units=metric&lang=fr'
    response = requests.get(url)
    data = response.json()

    # Ajouter un débogage pour afficher les données retournées
    print(data)  # Ajoute ceci pour voir la réponse brute

    if data['cod'] == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"🌤 La température à {ville} est de {temp}°C avec {description}."
    else:
        # Affiche le code d'erreur retourné par l'API pour aider au débogage
        return f"❌ Impossible de récupérer la météo pour {ville}. Code erreur : {data['cod']} - {data.get('message', 'Aucune information sur l\'erreur.')}"



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

    if "actualités du jour" in question or "news" in question:
        message_bot = f"📰 Voici les actualités générales du jour :\n\n{get_general_news()}"
    
    elif "météo" in question or "quel temps" in question:
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

