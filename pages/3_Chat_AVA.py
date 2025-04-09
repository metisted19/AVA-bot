import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import pytz
import requests
import streamlit as st
import requests

# Remplace par ta clé API OpenWeatherMap
API_KEY = 'ta_vraie_clé_API'

# Fonction pour récupérer la météo
def get_meteo_ville(ville):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY}&units=metric&lang=fr'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"🌤 La température à {ville} est de {temp}°C avec {description}."
    else:
        return f"❌ Impossible de récupérer la météo pour {ville}. Code erreur : {data['cod']} - {data.get('message', 'Aucune information sur l\'erreur.')}"


# Zone d'historique du chat
if "historique" not in st.session_state:
    st.session_state.historique = []

# Champ de saisie utilisateur
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

# Traitement du message
if user_input:
    question = user_input.lower().strip()  # Normaliser la question de l'utilisateur
    message_bot = ""  # Initialiser la réponse du bot

    if "météo" in question or "quel temps" in question:
        ville = "Paris"  # Ville par défaut, tu pourrais demander à l'utilisateur d'entrer une ville
        meteo = get_meteo_ville(ville)
        message_bot = meteo
    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    # Ajout à l'historique des messages
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# Affichage de l'historique
if st.session_state.historique:
    for auteur, message in st.session_state.historique:
        with st.chat_message(auteur):
            st.markdown(message)
