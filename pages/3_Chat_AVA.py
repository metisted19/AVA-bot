import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville
import requests
import random

# Configuration de la page Streamlit
st.set_page_config(page_title="Chat AVA", layout="centered")

st.title("🤖 AVA - Chat IA")
st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités... ou juste pour discuter !")

# Initialisation de l'historique de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Affichage des messages existants ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Blagues, punchlines et citations ---
def get_random_fun_content(type="blague"):
    blagues = [
        "Pourquoi les traders ne bronzent jamais ? Parce qu'ils restent à l'ombre des graphes !",
        "Je connais un trader qui a vendu sa maison pour acheter du Bitcoin... Maintenant il vit dans le cloud ☁️",
        "Pourquoi l'IA n'a jamais peur ? Parce qu'elle ne manque jamais de logique."
    ]
    punchlines = [
        "Je suis AVA, l'alliée des cerveaux affûtés et des marchés en ébullition ✨",
        "Je prédis les tendances comme un mage des temps modernes.",
        "Aucune rumeur ne m'échappe, aucune bougie ne me ment."
    ]
    citations = [
        """"Le succès appartient à ceux qui sont prêts à apprendre, chaque jour." - AVA""",
        """"L'information, c'est le pouvoir. L'analyse, c'est la clé." - AVA""",
        """"Reste calme quand le marché s'agite. C'est là que se créent les opportunités." - AVA"""
    ]
    if type == "blague":
        return random.choice(blagues)
    elif type == "punchline":
        return random.choice(punchlines)
    else:
        return random.choice(citations)

# --- Interaction principale ---
question = st.chat_input("Que souhaitez-vous demander à AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        question_clean = question.lower().strip()
        message_bot = ""

        # --- Horoscope ---
        if "horoscope" in question_clean or "signe" in question_clean or "astrologie" in question_clean:
            signes = ["bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance", "scorpion", "sagittaire", "capricorne", "verseau", "poissons"]
            signe_detecte = next((s for s in signes if s in question_clean), None)

            if not signe_detecte:
                message_bot = "🔮 Pour vous donner votre horoscope, indiquez-moi votre **signe astrologique** (ex : Lion, Vierge...)."
            else:
                try:
                    url = f"https://aztro.sameerkumar.website/?sign={signe_detecte}&day=today"
                    response = requests.post(url)
                    if response.status_code == 200:
                        data = response.json()
                        message_bot = f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {data['description']}"
                    else:
                        message_bot = "❌ Désolé, impossible d'obtenir l'horoscope pour le moment."
                except Exception as e:
                    message_bot = f"⚠️ Une erreur est survenue : {e}"

        # --- Blagues & punchlines ---
        elif any(mot in question_clean for mot in ["blague", "rigole", "fais-moi rire"]):
            message_bot = get_random_fun_content("blague")
        elif "punchline" in question_clean:
            message_bot = get_random_fun_content("punchline")
        elif any(mot in question_clean for mot in ["citation", "motivation", "inspire"]):
            message_bot = get_random_fun_content("citation")

        # --- Actualités ---
        elif "actualité" in question_clean or "news" in question_clean:
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot = actus
            elif actus:
                message_bot = "🕴️ Voici les actualités :\n\n" + "\n\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus])
            else:
                message_bot = "❌ Aucune actualité disponible pour le moment."

        # --- Météo ---
        elif "météo" in question_clean or "quel temps" in question_clean:
            ville_detectee = "Paris"
            for mot in question.split():
                if mot and mot[0].isupper() and len(mot) > 2:
                    ville_detectee = mot
            message_bot = get_meteo_ville(ville_detectee)

        # --- Réponses simples ---
        elif any(phrase in question_clean for phrase in ["ça va", "comment tu vas", "tu vas bien"]):
            message_bot = "Je vais super bien, prête à analyser le monde avec vous ! Et vous ?"

        elif any(phrase in question_clean for phrase in ["quoi de neuf", "tu fais quoi", "des news"]):
            message_bot = "Je scrute les marchés, je capte les tendances… une journée normale pour une IA boursière !"

        elif any(phrase in question_clean for phrase in ["t'es qui", "tu es qui", "t'es quoi", "tu es quoi"]):
            message_bot = "Je suis AVA, votre assistante virtuelle boursière, météo, et bien plus. Disons... une alliée du futur."

        elif any(phrase in question_clean for phrase in ["tu dors", "t'es là", "tu es là"]):
            message_bot = "Je ne dors jamais. Toujours connectée, toujours prête. Posez votre question !"

        elif "salut" in question_clean or "bonjour" in question_clean:
            message_bot = "👋 Bonjour ! Je suis AVA. Besoin d'une analyse ou d'un coup de pouce ? 😊"

        # --- Analyse technique vivante ---
        elif any(symb in question_clean for symb in ["aapl", "tsla", "googl", "btc", "bitcoin", "eth", "fchi", "cac"]):
            nom_ticker = question_clean.replace(" ", "").replace("-", "")
            if "btc" in nom_ticker or "bitcoin" in nom_ticker:
                nom_ticker = "btc-usd"
            elif "eth" in nom_ticker:
                nom_ticker = "eth-usd"
            elif "aapl" in nom_ticker:
                nom_ticker = "aapl"
            elif "tsla" in nom_ticker:
                nom_ticker = "tsla"
            elif "googl" in nom_ticker:
                nom_ticker = "googl"
            elif "fchi" in nom_ticker or "cac" in nom_ticker:
                nom_ticker = "^fchi"

            data_path = f"data/donnees_{nom_ticker}.csv"
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                df.columns = [col.capitalize() for col in df.columns]
                try:
                    analyse, suggestion = analyser_signaux_techniques(df)
                    message_bot = (
                        f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n"
                        f"{analyse}\n\n"
                        f"🤖 *Mon intuition d'IA ?* {suggestion}"
                    )
                except Exception as e:
                    message_bot = f"⚠️ Une erreur est survenue pendant l'analyse : {e}"
            else:
                message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}.\nLancez le script d'entraînement pour les générer."

        else:
            message_bot = obtenir_reponse_ava(question)

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

# Bouton pour effacer les messages uniquement
st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))



















