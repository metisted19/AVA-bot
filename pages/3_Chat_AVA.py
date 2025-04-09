import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import pytz
import requests

# Remplace par ta clé API OpenWeatherMap
API_KEY = 'ton_api_key_ici'

def get_meteo_ville(ville):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY}&units=metric&lang=fr'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"🌤 La température à {ville} est de {temp}°C avec {description}."
    else:
        return "❌ Impossible de récupérer la météo pour cette ville."

# Exemple d'intégration dans le chatbot AVA
if "météo" in question or "quel temps" in question:
    # Demander la ville, ou mettre une valeur par défaut
    ville = "Paris"  # Remplacer par la ville souhaitée ou par une question du user
    meteo = get_meteo_ville(ville)
    message_bot = meteo

# Accès au module utils/analyse_technique.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.analyse_technique import analyse_signaux

# Configuration de la page
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# Chargement des données
@st.cache_data
def charger_donnees(path):
    df = pd.read_csv(path)
    if 'date' not in df.columns:
        df.reset_index(inplace=True)
    if 'Date' in df.columns and 'date' not in df.columns:
        df.rename(columns={'Date': 'date'}, inplace=True)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
    return df

# Sélection d’actif
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("📌 Choisissez un actif :", tickers)

# Zone d'historique du chat
if "historique" not in st.session_state:
    st.session_state.historique = []

# Bouton pour effacer l'historique
if st.button("🗑️ Effacer la conversation"):
    st.session_state.historique = []
    st.experimental_rerun()

# Champ de saisie utilisateur
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

# Traitement du message
if user_input:
    data_path = f"data/donnees_{ticker.lower()}.csv"
    message_bot = ""

    if os.path.exists(data_path):
        df = charger_donnees(data_path)
        question = user_input.lower().strip()

        corrections = {
            "analize": "analyse", "matéo": "météo", "rci": "rsi",
            "mercie": "merci", "blag": "blague"
        }
        for faute, correction in corrections.items():
            question = question.replace(faute, correction)

        if "bonjour" in question or "salut" in question:
            message_bot = "Bonjour 👋 ! Je suis ravie de vous retrouver. Une question sur les marchés ? Ou juste envie de discuter ? 😊"
        elif "merci" in question:
            message_bot = "Avec plaisir 💙 ! N’hésitez pas à me solliciter dès que vous avez besoin."
        elif "tu es qui" in question:
            message_bot = "Je suis AVA, votre copilote boursier personnel 🤖. J’analyse les marchés pour vous guider au mieux !"
        elif any(mot in question for mot in ["analyse", "avis", "penses", "analyse technique"]):
            message_bot = f"🔍 Mon analyse technique pour **{ticker}** :\n\n" + analyse_signaux(df)
        elif "heure" in question:
            heure = datetime.now(pytz.timezone("Europe/Paris")).strftime("%H:%M")
            message_bot = f"🕒 Il est **{heure}** à Paris."
        elif "date" in question:
            date = datetime.now(pytz.timezone("Europe/Paris")).strftime("%A %d %B %Y")
            message_bot = f"📅 Aujourd’hui, nous sommes le **{date}**."
        elif "météo" in question:
            message_bot = "🌤 Je ne suis pas encore connectée à la météo réelle... mais je sens qu’il fait **beau pour investir** aujourd’hui !"
        elif "blague" in question:
            message_bot = "Pourquoi les traders utilisent-ils toujours Google ? Parce qu’ils veulent toujours être dans la tendance ! 📉😄"
        elif any(mot in question for mot in ["motivation", "fatigué", "booster", "démotivé"]):
            message_bot = "💪 Même les marchés consolident parfois. Reprenez des forces, la prochaine bougie verte est peut-être pour vous 🚀."
        elif any(mot in question for mot in ["punchline", "avenir", "vision", "futur"]):
            message_bot = "🔮 Mon IA scrute les lignes de code et de tendance... Je ne prédis pas l’avenir, je l’**analyse** 📊✨."
        else:
            message_bot = "Je n’ai pas encore appris à répondre à cela… Essayez avec *analyse technique*, *heure*, *blague*, ou *météo* 🌍"
    else:
        message_bot = f"⚠️ Je n’ai pas trouvé les données pour {ticker}. Pensez à lancer le script d'entraînement."

    # Historique
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# Affichage de l'historique
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)

