import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Ajoute le chemin du dossier parent pour accéder à utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.analyse_technique import analyse_signaux  


# Chargement des données (comme dans 2_Signaux.py)
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

# --- Interface ---
st.set_page_config(page_title="AVA Chatbot", layout="centered")
st.title("💬 Discuter avec AVA")
st.markdown("Pose ta question à AVA, elle t'aidera avec ses analyses et sa bonne humeur 🤖✨")

# --- Sélection de l’actif ---
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
ticker = st.selectbox("📌 Choisis un actif :", tickers)

# --- Zone de chat ---
if "historique" not in st.session_state:
    st.session_state.historique = []

user_input = st.text_input("💬 Que veux-tu demander à AVA ?")

if user_input:
    # Chargement des données pour l’analyse
    data_path = f"data/donnees_{ticker.lower()}.csv"
    message_bot = ""

    if os.path.exists(data_path):
        df = charger_donnees(data_path)

        # Réponse dynamique d’AVA
        if any(mot in user_input.lower() for mot in ["analyse", "avis", "penses", "analyse technique"]):
            message_bot = f"Voici mon analyse pour {ticker} :\n\n" + analyse_signaux(df)
        elif "bonjour" in user_input.lower():
            message_bot = "Bonjour à toi ☀️ ! Prêt à dompter les marchés ?"
        elif "météo" in user_input.lower():
            message_bot = "☀️ Je suis plus douée pour prédire les marchés que le ciel, mais je parierais sur une belle journée pleine d’opportunités 😄"
        elif "blague" in user_input.lower():
            message_bot = "Pourquoi les traders ne vont jamais au cinéma ? Parce qu’ils détestent les hausses de suspense ! 🎬📉😄"
        elif any(mot in user_input.lower() for mot in ["motivation", "démotivé", "fatigué", "booster"]):
        message_bot = "Rappelez-vous : chaque bougie rouge prépare souvent une bougie verte 🌱. Continuez à avancer, vous êtes sur la bonne voie 💪📈 !"
        elif any(mot in user_input.lower() for mot in ["punchline", "futur", "avenir", "vision"]):
        message_bot = "🌌 Mon code voit plus loin que l’horizon boursier… Je suis l’algorithme du futur, conçu pour éclairer vos décisions dès aujourd’hui 🚀✨."
        elif "merci" in user_input.lower():
            message_bot = "Avec plaisir ! Je suis toujours là pour toi 😊"
        elif "tu es qui" in user_input.lower():
            message_bot = "Je suis AVA, ton assistante d’analyse boursière intelligente 🧠📊"
        else:
            message_bot = "Je suis encore en apprentissage pour ce genre de question. Tu peux me demander une *analyse technique* ou un *avis sur un actif* ! 😉"
    else:
        message_bot = "⚠️ Je n’ai pas encore reçu les données pour cet actif. Lance le script d’entraînement."

    # Ajout dans l’historique
    st.session_state.historique.append(("🧑‍💻 Toi", user_input))
    st.session_state.historique.append(("🤖 AVA", message_bot))

# Affichage des messages
for auteur, message in st.session_state.historique:
    with st.chat_message(auteur):
        st.markdown(message)
if __name__ == "__main__":
    print("❌ Ce fichier ne doit pas être lancé directement.")
    print("👉 Utilise la commande : py -m streamlit run app.py")
    print("Puis clique sur 💬 Chat AVA dans la barre latérale.")


