import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville
import requests
from PIL import Image
from datetime import datetime
from langdetect import detect
import urllib.parse
import random

# Fonction de traduction via l’API gratuite MyMemory
def traduire_texte(texte, langue_dest):
    try:
        texte_enc = urllib.parse.quote(texte)
        url = f"https://api.mymemory.translated.net/get?q={texte_enc}&langpair=fr|{langue_dest}"
        r = requests.get(url).json()
        return r["responseData"]["translatedText"]
    except:
        return texte  # fallback

# Fonction humeur dynamique selon l'heure
def humeur_du_jour():
    heure = datetime.now().hour
    if heure < 8:
        return "😴 Pas très bavarde ce matin, mais je suis là pour vous servir !"
    elif heure < 12:
        return "☕ Pleine d'énergie pour cette matinée ! Une analyse avec ça ?"
    elif heure < 17:
        return "💼 Focus total sur les marchés, on décortique tout ensemble !"
    elif heure < 21:
        return "🧘 Détendue mais toujours efficace. Prêt(e) pour une analyse zen ?"
    else:
        return "🌙 En mode nocturne, mais toujours connectée pour vous aider !"

# Configuration de la page Streamlit
st.set_page_config(page_title="Chat AVA", layout="centered")

# Message d'accueil dynamique selon l'heure
heure_actuelle = datetime.now().hour
if heure_actuelle < 12:
    accueil = "🌞 Bonjour ! Prêt(e) pour une nouvelle journée de trading ?"
elif 12 <= heure_actuelle < 18:
    accueil = "☀️ Bon après-midi ! Besoin d’une analyse ou d’un conseil ?"
else:
    accueil = "🌙 Bonsoir ! On termine la journée avec une petite analyse ?"

# Affichage du message d'accueil avec logo personnalisé
col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image("assets/ava_logo.png", width=60)
with col2:
    st.markdown(f"<h1 style='margin-top: 10px;'>AVA - Chat IA</h1><p>{accueil}</p>", unsafe_allow_html=True)

st.markdown(f"<p style='font-style: italic;'>{humeur_du_jour()}</p>", unsafe_allow_html=True)
st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités... ou juste pour discuter !")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="assets/ava_logo.png"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

question = st.chat_input("Que souhaitez-vous demander à AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="assets/ava_logo.png"):
        question_clean = question.lower().strip()
        message_bot = ""

        horoscope_repondu = False
        meteo_repondu = False
        actus_repondu = False

        # Horoscope
        if any(mot in question_clean for mot in ["horoscope", "signe", "astrologie"]):
            signes = ["bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance", "scorpion", "sagittaire", "capricorne", "verseau", "poissons"]
            signes_api = {
                "bélier": "aries", "taureau": "taurus", "gémeaux": "gemini",
                "cancer": "cancer", "lion": "leo", "vierge": "virgo",
                "balance": "libra", "scorpion": "scorpio", "sagittaire": "sagittarius",
                "capricorne": "capricorn", "verseau": "aquarius", "poissons": "pisces"
            }
            signe_detecte = next((s for s in signes if s in question_clean), None)
            if not signe_detecte:
                message_bot += "🔮 Pour l'horoscope, indiquez-moi votre **signe astrologique**.\n\n"
            else:
                try:
                    signe_api = signes_api.get(signe_detecte, "")
                    url = f"https://aztro.sameerkumar.website/?sign={signe_api}&day=today"
                    response = requests.post(url)
                    if response.status_code == 200:
                        data = response.json()
                        message_bot += f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {data['description']}\n\n"
                        horoscope_repondu = True
                except:
                    message_bot += "❌ Erreur lors de la récupération de l'horoscope.\n\n"

        # Actualités
        if "actualité" in question_clean or "news" in question_clean:
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot += actus
            elif actus:
                resume = "".join([titre for titre, _ in actus[:3]])
                message_bot += "🧔️ Les actus bougent ! Voici un résumé :\n\n"
                message_bot += f"*En bref* : {resume[:180]}...\n\n"
                message_bot += "🔖 Articles à lire :\n" + "\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus]) + "\n\n"
                actus_repondu = True

        # Météo
        if "météo" in question_clean or "quel temps" in question_clean:
            ville_detectee = "Paris"
            for mot in question.split():
                if mot and mot[0].isupper() and len(mot) > 2:
                    ville_detectee = mot
            meteo = get_meteo_ville(ville_detectee)
            message_bot += f"🌦️ Météo à {ville_detectee} :\n{meteo}\n\n"
            meteo_repondu = True

        # Réponses simples, blagues, motivation
        elif any(phrase in question_clean for phrase in ["blague", "blagues"]):
            blagues = [
                "Pourquoi les traders n'ont jamais froid ? Parce qu’ils ont toujours des bougies japonaises ! 😂",
                "Quel est le comble pour une IA ? Tomber en panne pendant une mise à jour 😅",
                "Pourquoi le Bitcoin fait du yoga ? Pour rester stable... mais c'est pas gagné ! 🧘‍♂️"
            ]
            message_bot = random.choice(blagues)

        elif any(phrase in question_clean for phrase in ["motivation", "boost", "conseil"]):
            message_bot = "🚀 N'oubliez jamais : les plus grandes réussites partent souvent d’une simple idée… AVA en est la preuve vivante."

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

        elif not any([horoscope_repondu, meteo_repondu, actus_repondu]):
            if any(symb in question_clean for symb in ["aapl", "tsla", "googl", "btc", "bitcoin", "eth", "fchi", "cac"]):
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
                            f"📈 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n"
                            f"{analyse}\n\n"
                            f"🧐 *Mon intuition d'IA ?* {suggestion}"
                        )
                    except Exception as e:
                        message_bot = f"⚠️ Une erreur est survenue pendant l'analyse : {e}"
                else:
                    message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}.\nLancez le script d'entraînement pour les générer."
            else:
                message_bot = obtenir_reponse_ava(question)

        try:
            langue = detect(question)
            if langue in ["en", "es", "de"]:
                message_bot = traduire_texte(message_bot, langue)
        except:
            message_bot += "\n\n⚠️ Traduction indisponible."

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

# Bouton pour effacer les messages uniquement
st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))




































