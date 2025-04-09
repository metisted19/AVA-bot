import streamlit as st
import requests
from datetime import datetime
import pytz

# Remplace avec ta vraie clé API OpenWeatherMap
API_KEY = 'ton_api_key_ici'  # Remplace cette ligne par la clé API valide

def get_meteo_ville(ville):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY}&units=metric&lang=fr'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"🌤 La température à {ville} est de {temp}°C avec {description}."
    else:
       return "❌ Impossible de récupérer la météo pour " + ville + ". Code erreur : " + str(data['cod']) + " - " + str(data.get('message', 'Aucune information sur l\'erreur.'))

data = response.json()
print(data)  # Cela affichera la réponse de l'API pour un débogage


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
