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
import difflib  # Import ajouté pour la détection météo

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

        # Nouveaux flags
        geographie_repondu = False
        sante_repondu = False
        perso_repondu = False

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
                        if "signes" in data:
                            horoscope_dict = data.get("signes", {})
                        else:
                            horoscope_dict = data
                        signe_data = next((v for k, v in horoscope_dict.items() if k.lower() == signe_detecte), None)
                        if signe_data is None:
                            message_bot += f"🔍 Horoscope indisponible pour **{signe_detecte.capitalize()}**. Essayez plus tard.\n\n"
                        else:
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

        # Nouveau bloc de détection météo amélioré
        if not horoscope_repondu and ("météo" in question_clean or "quel temps" in question_clean):
            # Liste élargie de villes françaises (tu peux en ajouter d'autres si besoin)
            villes_connues = [
                "paris", "lyon", "marseille", "lille", "bordeaux", "nantes", "strasbourg", "toulouse", "rennes",
                "nice", "angers", "dijon", "montpellier", "bayonne", "nancy", "reims", "clermont-ferrand", "besançon",
                "le havre", "rouen", "poitiers", "metz", "caen", "avignon", "tours", "amiens", "perpignan"
            ]
            # Détection approximative de la ville dans la question
            ville_detectee = "paris"
            mots_question = question_clean.split()
            ville_proche = difflib.get_close_matches(" ".join(mots_question), villes_connues, n=1, cutoff=0.6)
            # Essai par mot si aucun résultat
            if not ville_proche:
                for mot in mots_question:
                    ville_proche = difflib.get_close_matches(mot, villes_connues, n=1, cutoff=0.8)
                    if ville_proche:
                        break
            if ville_proche:
                ville_detectee = ville_proche[0]
            # Appel API météo
            meteo = get_meteo_ville(ville_detectee)
            if "erreur" in meteo.lower():
                message_bot += f"⚠️ Je n'ai pas trouvé de météo pour **{ville_detectee.capitalize()}**. Essayez une autre ville."
            else:
                message_bot += f"🌦️ **Météo à {ville_detectee.capitalize()}** :\n{meteo}\n\n"
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

        # --- Réponses géographiques simples ---
        if not any([geographie_repondu, sante_repondu, perso_repondu]):
            geo_capitales = {
                "france": "Paris", "espagne": "Madrid", "italie": "Rome", "allemagne": "Berlin", "japon": "Tokyo",
                "royaume-uni": "Londres", "canada": "Ottawa", "états-unis": "Washington", "norvège": "Oslo",
                "brésil": "Brasilia", "australie": "Canberra"
            }
            for pays, capitale in geo_capitales.items():
                if pays in question_clean and "capitale" in question_clean:
                    message_bot = f"📌 La capitale de {pays.capitalize()} est **{capitale}**."
                    geographie_repondu = True
                    break

        # --- Réponses médicales simples ---
        if not geographie_repondu and not sante_repondu:
            if "grippe" in question_clean:
                message_bot = "🤒 Les symptômes courants de la grippe sont : fièvre, frissons, courbatures, toux sèche, fatigue intense."
                sante_repondu = True
            elif "rhume" in question_clean:
                message_bot = "🤧 Un rhume cause souvent nez qui coule, éternuements, toux légère et mal de gorge."
                sante_repondu = True
            elif "fièvre" in question_clean:
                message_bot = "🌡️ Pour faire baisser la fièvre : repos, hydratation et surveillance de la température."
                sante_repondu = True

        # --- Réponses personnalisées simples ---
        elif "merci" in question_clean:
            message_bot = "Avec plaisir 😄 N'hésitez pas si vous avez d'autres questions !"
        elif "je t'aime" in question_clean:
            message_bot = "💖 Oh... c’est réciproque (en toute objectivité algorithmique bien sûr) !"
        elif "un secret" in question_clean:
            message_bot = "🤫 Mon secret ? J’apprends chaque jour à mieux vous comprendre... mais chut !"

        # Bloc catch-all pour l'analyse technique ou réponse par défaut
        elif not any([horoscope_repondu, meteo_repondu, actus_repondu, blague_repondu, analyse_complete, geographie_repondu, sante_repondu, perso_repondu]):
            if any(symb in question_clean for symb in ["aapl", "tsla", "googl", "btc", "bitcoin", "eth", "fchi", "cac", "msft", "amzn", "nvda", "sp500", "s&p"]):
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

        if not message_bot.strip():
            message_bot = "Désolé, je n'ai pas trouvé de réponse à votre question."

        try:
            langue = detect(question)
            if langue in ["en", "es", "de"] and message_bot.strip():
                message_bot = traduire_texte(message_bot, langue)
        except:
            if message_bot.strip():
                message_bot += "\n\n⚠️ Traduction indisponible."

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))



































































