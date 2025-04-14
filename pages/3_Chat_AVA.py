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
import glob

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
        return "😬 Pas très bavarde ce matin, mais je suis là pour vous servir !"
    elif heure < 12:
        return "☕ Pleine d'énergie pour cette matinée ! Une analyse avec ça ?"
    elif heure < 17:
        return "💼 Focus total sur les marchés, on décortique tout ensemble !"
    elif heure < 21:
        return "🧘 Détendue mais toujours efficace. Prêt(e) pour une analyse zen ?"
    else:
        return "🌙 En mode nocturne, mais toujours connectée pour vous aider !"

st.set_page_config(page_title="Chat AVA", layout="centered")

heure_actuelle = datetime.now().hour
if heure_actuelle < 12:
    accueil = "🌞 Bonjour ! Prêt(e) pour une nouvelle journée de trading ?"
elif 12 <= heure_actuelle < 18:
    accueil = "☀️ Bon après-midi ! Besoin d’une analyse ou d’un conseil ?"
else:
    accueil = "🌙 Bonsoir ! On termine la journée avec une petite analyse ?"

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
        blague_repondu = False
        analyse_complete = False

        # Partie horoscope avec gestion insensible à la casse et adaptation du format JSON
        if any(mot in question_clean for mot in ["horoscope", "signe", "astrologie"]):
            signes_disponibles = [
                "bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance",
                "scorpion", "sagittaire", "capricorne", "verseau", "poissons"
            ]
            signe_detecte = next((s for s in signes_disponibles if s in question_clean), None)
            if not signe_detecte:
                message_bot += "🔮 Pour vous donner votre horoscope, indiquez-moi votre **signe astrologique** (ex : Lion, Vierge...).\n\n"
                horoscope_repondu = True
            else:
                try:
                    url = "https://kayoo123.github.io/astroo-api/jour.json"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        # Si la clé "signes" existe, on prend son contenu, sinon on considère le JSON entier comme le dictionnaire d'horoscopes.
                        if "signes" in data:
                            horoscope_dict = data.get("signes", {})
                        else:
                            horoscope_dict = data
                        # Recherche du signe de façon insensible à la casse dans les clés
                        signe_data = next((v for k, v in horoscope_dict.items() if k.lower() == signe_detecte), None)
                        if signe_data is None:
                            message_bot += f"🔍 Horoscope indisponible pour **{signe_detecte.capitalize()}**. Essayez plus tard.\n\n"
                        else:
                            # Si la donnée est un dictionnaire, on récupère la clé "horoscope", sinon on prend la valeur directement
                            if isinstance(signe_data, dict):
                                horoscope = signe_data.get("horoscope")
                            else:
                                horoscope = signe_data
                            if horoscope:
                                message_bot += f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {horoscope}\n\n"
                            else:
                                message_bot += f"🔍 Horoscope indisponible pour **{signe_detecte.capitalize()}**. Essayez plus tard.\n\n"
                        horoscope_repondu = True
                    else:
                        message_bot += "❌ Impossible d'obtenir l'horoscope pour le moment.\n\n"
                        horoscope_repondu = True
                except Exception as e:
                    message_bot += "⚠️ Une erreur est survenue lors de la récupération de l'horoscope.\n\n"
                    horoscope_repondu = True

        if not horoscope_repondu and any(phrase in question_clean for phrase in ["analyse complète", "analyse des marchés", "analyse technique", "prévision boursière"]):
            try:
                resultats = []
                fichiers = glob.glob("data/donnees_*.csv")
                for fichier in fichiers:
                    df = pd.read_csv(fichier)
                    df.columns = [col.capitalize() for col in df.columns]
                    df = ajouter_indicateurs_techniques(df)  # ← Important !
                    analyse, suggestion = analyser_signaux_techniques(df)
                    try:
                        analyse, suggestion = analyser_signaux_techniques(df)
                        nom = fichier.split("donnees_")[1].replace(".csv", "").upper()
                        resume = f"\n📌 **{nom}**\n{analyse}\n📁 {suggestion}"
                        resultats.append(resume)
                    except:
                        continue
                if resultats:
                    message_bot += "📊 **Analyse complète du marché :**\n" + "\n\n".join(resultats) + "\n\n"
                    analyse_complete = True
            except Exception as e:
                message_bot += f"❌ Erreur lors de l'analyse complète : {e}\n\n"

        if not horoscope_repondu and ("météo" in question_clean or "quel temps" in question_clean):
            ville_detectee = "Paris"
            for mot in question.split():
                if mot and mot[0].isupper() and len(mot) > 2:
                    ville_detectee = mot
            meteo = get_meteo_ville(ville_detectee)
            message_bot += f"🌦️ Météo à {ville_detectee} :\n{meteo}\n\n"
            meteo_repondu = True

        if not horoscope_repondu and ("actualité" in question_clean or "news" in question_clean):
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot += actus
            elif actus:
                resume = "".join([titre for titre, _ in actus[:3]])
                message_bot += "🧔️ Les actus bougent ! Voici un résumé :\n\n"
                message_bot += f"*En bref* : {resume[:180]}...\n\n"
                message_bot += "🔖 Articles à lire :\n" + "\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus]) + "\n\n"
                actus_repondu = True

        elif not horoscope_repondu and any(phrase in question_clean for phrase in ["blague", "blagues"]):
            blagues = [
                "Pourquoi les traders n'ont jamais froid ? Parce qu’ils ont toujours des bougies japonaises ! 😂",
                "Quel est le comble pour une IA ? Tomber en panne pendant une mise à jour 😅",
                "Pourquoi le Bitcoin fait du yoga ? Pour rester stable... mais c'est pas gagné ! 🧘‍♂️"
            ]
            message_bot = random.choice(blagues)
            blague_repondu = True

        elif not any([horoscope_repondu, meteo_repondu, actus_repondu, blague_repondu, analyse_complete]):
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
                elif "msft" in nom_ticker:
                    nom_ticker = "msft"
                elif "amzn" in nom_ticker:
                    nom_ticker = "amzn"
                elif "nvda" in nom_ticker:
                    nom_ticker = "nvda"
                elif "sp500" in nom_ticker or "s&p" in nom_ticker:
                    nom_ticker = "gspc"

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

        if not blague_repondu:
            try:
                langue = detect(question)
                if langue in ["en", "es", "de"]:
                    message_bot = traduire_texte(message_bot, langue)
            except:
                message_bot += "\n\n⚠️ Traduction indisponible."

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))





























































