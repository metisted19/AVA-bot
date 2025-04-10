import streamlit as st
import requests
from datetime import datetime
import pytz
from newsapi import NewsApiClient

# --- Clés API ---
API_KEY_METEO = "26b32c230513505762cb096f4d05b0cc"
API_KEY_NEWS = "681120bace124ee99d390cc059e6aca5"  # ta clé NewsAPI actuelle



def get_meteo_ville(ville):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY_METEO}&units=metric&lang=fr"
    response = requests.get(url)
    data = response.json()
    print(data)  # ➜ pour voir ce que l'API renvoie
    if data['cod'] == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"🌤 Il fait {temp}°C à {ville} avec {description}."
    else:
        return f"❌ Erreur météo : Code {data['cod']} - Message : {data.get('message', 'Erreur inconnue')}"

# Test
print(get_meteo_ville("Paris"))


# --- Fonction pour récupérer les actualités ---
def get_general_news():
    try:
        headlines = newsapi.get_top_headlines(language="fr", country="fr", page_size=3)
    print(headlines)
         except Exception as e:
    print("Erreur :", e)

        articles = headlines.get("articles", [])
        if articles:
            news_list = []
            for article in articles:
                titre = article.get("title", "Sans titre")
                lien = article.get("url", "#")
                news_list.append(f"🔹 [{titre}]({lien})")
            return "\n\n".join(news_list)
        else:
            return "❌ Aucune actualité disponible pour le moment."
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

# Zone d'historique
if "historique" not in st.session_state:
    st.session_state.historique = []

# Champ de saisie utilisateur
user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?", key="chat_input")

# Traitement du message
if user_input:
    question = user_input.lower().strip()
    message_bot = ""

    if "actualités" in question or "news" in question:
    message_bot = f"📰 Voici les actualités générales du jour :\n\n{get_general_news()}"


    elif "météo" in question or "quel temps" in question or "temps" in question:
        ville = "Paris"  # Ville par défaut
        message_bot = get_meteo_ville(ville)

    else:
        message_bot = "Je n'ai pas compris votre question, mais je peux vous aider avec les actualités ou la météo ! 😊"

    # Historique
    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# Affichage
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)