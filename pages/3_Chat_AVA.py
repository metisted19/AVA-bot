import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville  # Nous redéfinirons get_meteo_ville ci-dessous.
import requests
from PIL import Image
from datetime import datetime
from langdetect import detect
import urllib.parse
import random
import glob
import difflib
import re  # Import pour le bloc géographie

# Nouvelle fonction get_meteo_ville utilisant l'API OpenWeatherMap
def get_meteo_ville(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=3b2ff0b77dd65559ba4a1a69769221d5&units=metric&lang=fr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            description = data["weather"][0]["description"].capitalize()
            temperature = data["main"]["temp"]
            humidity = data["main"].get("humidity", "N/A")
            wind_speed = data["wind"].get("speed", "N/A")
            return f"{description} avec {temperature}°C, humidité : {humidity}%, vent : {wind_speed} m/s."
        else:
            return "Erreur: données météo non disponibles."
    except Exception as e:
        return "Erreur: " + str(e)

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
        # Traitement de la question en minuscule
        question_clean = question.lower().strip()
        message_bot = ""
        horoscope_repondu = False
        meteo_repondu = False
        actus_repondu = False
        blague_repondu = False
        analyse_complete = False

        # Nouveaux flags pour la géographie, la médecine et les réponses personnalisées
        geographie_repondu = False
        sante_repondu = False
        perso_repondu = False

        # --- Partie Horoscope ---
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

        # --- Analyse complète / technique ---
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

        # --- Bloc météo amélioré ---
        if not horoscope_repondu and ("météo" in question_clean or "quel temps" in question_clean):
            # Liste élargie de villes françaises
            villes_connues = [
                "paris", "lyon", "marseille", "lille", "bordeaux", "nantes", "strasbourg", "toulouse", "rennes",
                "nice", "angers", "dijon", "montpellier", "bayonne", "nancy", "reims", "clermont-ferrand", "besançon",
                "le havre", "rouen", "poitiers", "metz", "caen", "avignon", "tours", "amiens", "perpignan"
            ]
            # Détection approximative de la ville dans la question
            ville_detectee = "paris"
            mots_question = question_clean.split()
            ville_proche = difflib.get_close_matches(" ".join(mots_question), villes_connues, n=1, cutoff=0.6)
            if not ville_proche:
                for mot in mots_question:
                    ville_proche = difflib.get_close_matches(mot, villes_connues, n=1, cutoff=0.8)
                    if ville_proche:
                        break
            if ville_proche:
                ville_detectee = ville_proche[0]
            # Capitaliser le nom de la ville pour l'appel API
            ville_detectee_cap = ville_detectee.capitalize()
            # Appel API météo
            meteo = get_meteo_ville(ville_detectee_cap)
            if "erreur" in meteo.lower():
                message_bot += f"⚠️ Je n'ai pas trouvé de météo pour **{ville_detectee_cap}**. Essayez une autre ville."
            else:
                message_bot += f"🌦️ **Météo à {ville_detectee_cap}** :\n{meteo}\n\n"
            meteo_repondu = True

        # --- Actualités ---
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

        # --- Blagues ---
        elif not horoscope_repondu and any(phrase in question_clean for phrase in ["blague", "blagues"]):
            blagues = [
                "Pourquoi les traders n'ont jamais froid ? Parce qu’ils ont toujours des bougies japonaises ! 😂",
                "Quel est le comble pour une IA ? Tomber en panne pendant une mise à jour 😅",
                "Pourquoi le Bitcoin fait du yoga ? Pour rester stable... mais c'est pas gagné ! 🧘‍♂️"
            ]
            message_bot = random.choice(blagues)
            blague_repondu = True

        # --- Bloc Bonus: Analyse des phrases floues liées à des symptômes courants ---
        if not message_bot and any(phrase in question_clean for phrase in [
            "mal à la tête", "maux de tête", "j'ai de la fièvre", "fièvre", "mal à la gorge",
            "mal au ventre", "toux", "je tousse", "je suis enrhumé", "nez bouché", "j'ai chaud", "je transpire", "j'ai froid"
        ]):
            if "tête" in question_clean:
                message_bot = "🧠 Vous avez mal à la tête ? Cela peut être une migraine, une fatigue ou une tension. Essayez de vous reposer et hydratez-vous bien."
            elif "fièvre" in question_clean or "j'ai chaud" in question_clean:
                message_bot = "🌡️ La fièvre est un signal du corps contre une infection. Restez hydraté, reposez-vous et surveillez votre température."
            elif "gorge" in question_clean:
                message_bot = "👄 Un mal de gorge peut venir d’un rhume ou d’une angine. Buvez chaud, évitez de forcer sur la voix."
            elif "ventre" in question_clean:
                message_bot = "🍽️ Maux de ventre ? Peut-être digestif. Allégez votre repas, buvez de l’eau tiède, et reposez-vous."
            elif "toux" in question_clean or "je tousse" in question_clean:
                message_bot = "😷 Une toux persistante mérite repos et hydratation. Si elle dure plus de 3 jours, pensez à consulter."
            elif "nez" in question_clean:
                message_bot = "🤧 Nez bouché ? Un bon lavage au sérum physiologique et une boisson chaude peuvent aider à dégager les voies nasales."
            elif "transpire" in question_clean or "j'ai froid" in question_clean:
                message_bot = "🥶 Des frissons ? Cela peut être lié à une poussée de fièvre. Couvrez-vous légèrement, reposez-vous."

        # --- Bloc Remèdes naturels ---
        if not message_bot and any(phrase in question_clean for phrase in [
            "remède", "solution naturelle", "astuce maison", "traitement doux", "soulager naturellement", "tisane", "huile essentielle"
        ]):
            if "stress" in question_clean:
                message_bot = "🧘 Pour soulager le stress naturellement, pensez aux tisanes de camomille, à la respiration profonde ou à quelques minutes de méditation."
            elif "mal de gorge" in question_clean or "gorge" in question_clean:
                message_bot = "🍯 Un mal de gorge ? Une cuillère de miel dans une infusion au citron ou au thym peut faire des merveilles."
            elif "rhume" in question_clean or "nez bouché" in question_clean:
                message_bot = "🌿 Pour le nez bouché, essayez l'inhalation de vapeur avec quelques gouttes d’huile essentielle d’eucalyptus ou de menthe poivrée."
            elif "fièvre" in question_clean:
                message_bot = "🧊 En cas de fièvre, buvez beaucoup, reposez-vous et utilisez un linge frais sur le front. L’infusion de saule blanc est également un remède traditionnel."
            else:
                message_bot = "🌱 Il existe de nombreux remèdes naturels. Précisez votre souci (ex : toux, stress, rhume...) et je vous proposerai une solution douce."

        # --- Bloc Réponses médicales explicites ---
        elif not message_bot and any(mot in question_clean for mot in ["grippe", "rhume", "fièvre", "migraine", "angine", "hypertension", "stress", "toux", "maux", "douleur", "asthme", "bronchite"]):
            reponses_medic = {
                "grippe": "🤒 Les symptômes de la grippe incluent : fièvre élevée, frissons, fatigue intense, toux sèche, douleurs musculaires.",
                "rhume": "🤧 Le rhume provoque généralement une congestion nasale, des éternuements, une légère fatigue et parfois un peu de fièvre.",
                "fièvre": "🌡️ Pour faire baisser une fièvre, restez hydraté, reposez-vous, et prenez du paracétamol si besoin. Consultez si elle dépasse 39°C.",
                "migraine": "🧠 Une migraine est une douleur pulsatile souvent localisée d’un côté de la tête, pouvant s'accompagner de nausées et d'une sensibilité à la lumière.",
                "angine": "👄 L’angine provoque des maux de gorge intenses, parfois de la fièvre. Elle peut être virale ou bactérienne.",
                "hypertension": "❤️ L’hypertension est une pression sanguine trop élevée nécessitant un suivi médical et une hygiène de vie adaptée.",
                "stress": "🧘 Le stress peut se soulager par des techniques de relaxation ou une activité physique modérée.",
                "toux": "😷 Une toux sèche peut être le signe d'une irritation, tandis qu'une toux grasse aide à évacuer les sécrétions. Hydratez-vous bien.",
                "maux": "🤕 Précisez : maux de tête, de ventre, de dos ? Je peux vous donner des infos adaptées.",
                "douleur": "💢 Pour mieux vous aider, précisez la localisation ou l'intensité de la douleur.",
                "asthme": "🫁 L’asthme se caractérise par une inflammation des voies respiratoires et des difficultés à respirer, souvent soulagées par un inhalateur.",
                "bronchite": "🫁 La bronchite est une inflammation des bronches, souvent accompagnée d'une toux persistante et parfois de fièvre. Reposez-vous et hydratez-vous."
            }
            for cle, rep in reponses_medic.items():
                if cle in question_clean:
                    message_bot = rep
                    break

        # --- Bloc Réponses géographiques avec extraction par regex ---
        elif any(kw in question_clean for kw in ["capitale", "capitale de", "quelle est la capitale", "capitale du", "capitale de l", "capitale des"]):
            pays_detecte = None
            match = re.search(r"(?:de la|de l'|du|de|des)\s+([a-zàâçéèêëîïôûùüÿñæœ' -]+)", question_clean)
            if match:
                pays_detecte = match.group(1).strip()
            else:
                tokens = question_clean.split()
                if len(tokens) >= 2:
                    pays_detecte = tokens[-1].strip()  # Utilisation du dernier mot comme fallback
            capitales = {
                "france": "Paris",
                "espagne": "Madrid",
                "italie": "Rome",
                "allemagne": "Berlin",
                "japon": "Tokyo",
                "chine": "Pékin",
                "brésil": "Brasilia",
                "mexique": "Mexico",
                "canada": "Ottawa",
                "états-unis": "Washington",
                "usa": "Washington",
                "inde": "New Delhi",
                "portugal": "Lisbonne",
                "royaume-uni": "Londres",
                "angleterre": "Londres",
                "argentine": "Buenos Aires",
                "maroc": "Rabat",
                "algérie": "Alger",
                "tunisie": "Tunis",
                "turquie": "Ankara",
                "russie": "Moscou",
                "australie": "Canberra",
            }
            if pays_detecte and pays_detecte in capitales:
                capitale = capitales[pays_detecte]
                message_bot = f"📌 La capitale de {pays_detecte.capitalize()} est {capitale}."
            else:
                message_bot = "🌍 Je ne connais pas encore la capitale de ce pays. Essayez un autre !"

        # --- Bloc Réponses personnalisées simples ---
        elif not message_bot:
            if "merci" in question_clean:
                message_bot = "Avec plaisir 😄 N'hésitez pas si vous avez d'autres questions !"
            elif "je t'aime" in question_clean:
                message_bot = "💖 Oh... c’est réciproque (en toute objectivité algorithmique bien sûr) !"
            elif "un secret" in question_clean:
                message_bot = "🤫 Mon secret ? J’apprends chaque jour à mieux vous comprendre... mais chut !"

        # Bloc catch-all pour l'analyse technique ou réponse par défaut
        if not message_bot:
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
                elif "doge" in nom_ticker or "dogecoin" in nom_ticker:
                    nom_ticker = "doge-usd"
                elif "ada" in nom_ticker or "cardano" in nom_ticker:
                    nom_ticker = "ada-usd"

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



