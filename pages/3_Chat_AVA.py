from datetime import datetime
import pytz
import os
from newsapi import NewsApiClient
from utils.analyse_technique import analyse_signaux
import pandas as pd
import requests
import streamlit as st

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
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    # --- Actualités ---
    if "actualité" in question or "news" in question:
        actus = get_general_news()
        if isinstance(actus, str):  # Cas d'erreur
            message_bot = actus
        elif actus:
            message_bot = "📰 Voici les actualités :\n\n" + "\n\n".join(actus)
        else:
            message_bot = "❌ Aucune actualité disponible pour le moment."

    # --- Météo ---
    elif "météo" in question or "quel temps" in question:
        ville_detectee = "Paris"
        for mot in question.split():
            if mot[0].isupper() and len(mot) > 2:
                ville_detectee = mot
        message_bot = get_meteo_ville(ville_detectee)

    # --- Salutations ---
    elif "salut" in question or "bonjour" in question:
        message_bot = "👋 Bonjour ! Je suis AVA. Besoin d'une analyse ou d'un coup de pouce ? 😊"

        # --- Analyse technique ---
    elif any(symb in question for symb in ["aapl", "tsla", "googl", "btc", "eth"]):
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
        suggestion = ""
        if "rsi" in df.columns and df['rsi'].iloc[-1] < 30:
            suggestion = "💡 Le RSI est bas, cela pourrait indiquer une opportunité d'achat."
        elif "rsi" in df.columns and df['rsi'].iloc[-1] > 70:
            suggestion = "⚠️ Le RSI est élevé, cela pourrait signaler une zone de surachat."
        message_bot = f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n" + analyse_signaux(df)
        if suggestion:
            message_bot += f"\n\n{suggestion}"
    else:
        message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}. Lancez le script d'entraînement."

# --- Réponse par défaut ---
else:
    message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités, la météo ou une analyse technique ! 😊"

# --- Historique ---
st.session_state.historique.append(("🧑‍💻 Vous", user_input))
st.session_state.historique.append(("🤖 AVA", message_bot))

# --- Affichage de l'historique ---
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)
