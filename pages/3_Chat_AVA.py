import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Pour accéder au module utils/analyse_technique.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.analyse_technique import analyse_signaux

# --- Configuration de la page ---
st.set_page_config(page_title="Chat AVA", layout="centered")
st.title("💬 Bienvenue dans l'espace conversationnel d'AVA")

# --- Logo et description ---
st.image("ava_logo.png", width=100)
st.markdown("""
### 👋 Salut, je suis AVA  
Votre assistante boursière digitale. Posez-moi une question sur les marchés, ou parlez-moi de tout et de rien 😄
""")

# --- Chargement des données ---
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

# --- Sélection de l’actif ---
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("📌 Choisissez un actif :", tickers)

# --- Zone de chat ---
if "historique" not in st.session_state:
    st.session_state.historique = []

user_input = st.text_input("🧠 Que souhaitez-vous demander à AVA ?")

if user_input:
    data_path = f"data/donnees_{ticker.lower()}.csv"
    message_bot = ""

    if os.path.exists(data_path):
        df = charger_donnees(data_path)
        question = user_input.lower()

        # --- Analyse technique ---
        if any(mot in question for mot in ["analyse", "avis", "penses", "analyse technique"]):
            message_bot = f"🔍 Analyse technique pour {ticker} :\n\n" + analyse_signaux(df)

        # --- Heure ---
        elif "heure" in question:
            from datetime import datetime
            import pytz
            heure_actuelle = datetime.now(pytz.timezone("Europe/Paris")).strftime("%H:%M")
            message_bot = f"🕒 Il est actuellement {heure_actuelle} (heure de Paris)."

        # --- Date ---
        elif "date" in question:
            from datetime import datetime
            import pytz
            date_actuelle = datetime.now(pytz.timezone("Europe/Paris")).strftime("%A %d %B %Y")
            message_bot = f"📅 Aujourd’hui, nous sommes le {date_actuelle}."

        # --- Météo (simulée) ---
        elif "météo" in question:
            message_bot = "☁️ Je ne suis pas encore connectée à la météo en temps réel, mais je parie qu’il fait beau dans votre cœur ! 😄"

        # --- Blague ---
        elif "blague" in question:
            message_bot = "Pourquoi les traders ne vont jamais au cinéma ? Parce qu’ils détestent les hausses de suspense ! 🎬📉😄"

        # --- Motivation ---
        elif any(mot in question for mot in ["motivation", "fatigué", "booster", "démotivé"]):
            message_bot = "💡 Chaque bougie rouge prépare souvent une bougie verte. Gardez le cap, vous êtes plus près de la réussite que vous ne le pensez 💪📈"

        # --- Punchline futuriste ---
        elif any(mot in question for mot in ["punchline", "avenir", "vision", "futur"]):
            message_bot = "🌌 Mon code voit plus loin que l’horizon boursier… Je suis l’algorithme du futur, conçu pour éclairer vos décisions dès aujourd’hui 🚀✨."

        # --- Salutations ---
        elif "bonjour" in question:
            message_bot = "Bonjour à vous ☀️ ! Prêt à dompter les marchés avec moi ?"

        elif "merci" in question:
            message_bot = "Avec plaisir ! Je suis toujours là pour vous 😊"

        elif "tu es qui" in question:
            message_bot = "Je suis AVA, votre assistante d’analyse boursière intelligente 🧠📊"

        # --- Par défaut ---
        else:
            message_bot = "🤔 Je n’ai pas encore appris à répondre à cela. Essayez avec *analyse technique*, *heure*, *date*, ou même *blague* !"
    else:
        message_bot = "⚠️ Données manquantes pour cet actif. Lancez le script d’entraînement pour générer les prédictions."

    st.session_state.historique.append(("🧑‍💻 Vous", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# --- Affichage des échanges ---
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)

if __name__ == "__main__":
    print("❌ Ce fichier ne doit pas être lancé directement.")
    print("👉 Utilisez : py -m streamlit run app.py")




