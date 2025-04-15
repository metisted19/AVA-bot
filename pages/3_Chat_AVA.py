import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
# Remplacez cette importation par l'appel à la nouvelle version
#from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville  # Nous redéfinirons get_meteo_ville ici.
import requests
from PIL import Image
from datetime import datetime
from langdetect import detect
import urllib.parse
import random
import glob
import difflib
import re  # Pour le bloc sécurité, le traitement géographique et l'analyse
import unicodedata  # Pour supprimer les accents
from newsapi import NewsApiClient

# Fonction pour supprimer les accents d'une chaîne de caractères
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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

# Nouvelle fonction get_general_news() avec la modification pour NewsAPI
def get_general_news():
    try:
        # Définir la clé API directement ici
        api_key = "681120bace124ee99d390cc059e6aca5"
        newsapi = NewsApiClient(api_key=api_key)
        top_headlines = newsapi.get_top_headlines(country="us", page_size=10)
        if not top_headlines:
            return "❌ Aucune donnée reçue de NewsAPI. Vérifiez votre clé API et votre connexion."
        articles = top_headlines.get("articles")
        if not articles:
            return "❌ La réponse de NewsAPI ne contient pas d'articles."
        return [(article["title"], article["url"]) for article in articles if "title" in article and "url" in article]
    except Exception as e:
        return f"❌ Erreur lors de la récupération des actus via NewsApiClient : {e}"

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

# Récupération de la question utilisateur
question = st.chat_input("Que souhaitez-vous demander à AVA ?")

# 🔒 Sécurité : détection d'entrée dangereuse
if question and re.search(r"[<>;{}]", question):
    st.warning("⛔ Entrée invalide détectée.")
    st.stop()

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
            villes_connues = [
                "paris", "lyon", "marseille", "lille", "bordeaux", "nantes", "strasbourg", "toulouse", "rennes",
                "nice", "angers", "dijon", "montpellier", "bayonne", "nancy", "reims", "clermont-ferrand", "besançon",
                "le havre", "rouen", "poitiers", "metz", "caen", "avignon", "tours", "amiens", "perpignan"
            ]
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
            ville_detectee_cap = ville_detectee.capitalize()
            meteo = get_meteo_ville(ville_detectee_cap)
            if "erreur" in meteo.lower():
                message_bot += f"⚠️ Je n'ai pas trouvé de météo pour **{ville_detectee_cap}**. Essayez une autre ville."
            else:
                message_bot += f"🌦️ **Météo à {ville_detectee_cap}** :\n{meteo}\n\n"
            meteo_repondu = True

        # --- Actualités améliorées ---
        if not horoscope_repondu and ("actualité" in question_clean or "news" in question_clean):
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot += actus
            elif actus and isinstance(actus, list):
                message_bot += "📰 **Dernières actualités importantes :**\n\n"
                for i, (titre, lien) in enumerate(actus[:5], 1):
                    message_bot += f"{i}. 🔹 [{titre}]({lien})\n"
                message_bot += "\n🧠 *Restez curieux, le savoir, c’est la puissance !*"
            else:
                message_bot += "⚠️ Je n’ai pas pu récupérer les actualités pour le moment.\n\n"
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
        elif not message_bot and any(mot in question_clean for mot in ["grippe", "rhume", "fièvre", "migraine", "angine", "hypertension", "stress", "toux", "maux", "douleur", "asthme", "bronchite", "eczéma", "diabète", "cholestérol", "acné", "ulcère"]):
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
                "bronchite": "🫁 La bronchite est une inflammation des bronches, souvent accompagnée d'une toux persistante et parfois de fièvre. Reposez-vous et hydratez-vous.",
                "eczéma": "🩹 L’eczéma est une inflammation de la peau provoquant démangeaisons et rougeurs. Hydratez régulièrement et utilisez des crèmes apaisantes.",
                "diabète": "🩸 Le diabète affecte la régulation du sucre dans le sang. Un suivi médical, une alimentation équilibrée et une activité physique régulière sont essentiels.",
                "cholestérol": "🥚 Un taux élevé de cholestérol peut être réduit par une alimentation saine et de l'exercice. Consultez votre médecin pour un suivi personnalisé.",
                "acné": "💢 L'acné est souvent traitée par une bonne hygiène de la peau et, dans certains cas, des traitements spécifiques. Consultez un dermatologue si nécessaire.",
                "ulcère": "🩻 Les ulcères nécessitent un suivi médical attentif, une modification de l'alimentation et parfois des traitements médicamenteux spécifiques."
            }
            for cle, rep in reponses_medic.items():
                if cle in question_clean:
                    message_bot = rep
                    break

        # --- Bloc Réponses géographiques enrichi (restauré avec l'ancien bloc + pays en plus) ---
        elif any(kw in question_clean for kw in ["capitale", "capitale de", "capitale du", "capitale d", "capitale des", "où se trouve", "ville principale", "ville de"]):
            pays_detecte = None
            match = re.search(r"(?:de la|de l'|du|de|des)\s+([a-zàâçéèêëîïôûùüÿñæœ' -]+)", question_clean)
            if match:
                pays_detecte = match.group(1).strip().lower()
            else:
                tokens = question_clean.split()
                if len(tokens) >= 2:
                    pays_detecte = tokens[-1].strip(" ?!.,;").lower()
            capitales = {
                "france"           : "Paris",
                "espagne"          : "Madrid",
                "italie"           : "Rome",
                "allemagne"        : "Berlin",
                "japon"            : "Tokyo",
                "japonaise"        : "Tokyo",
                "chine"            : "Pékin",
                "brésil"           : "Brasilia",
                "mexique"          : "Mexico",
                "canada"           : "Ottawa",
                "états-unis"       : "Washington",
                "usa"              : "Washington",
                "united states"    : "Washington",
                "inde"             : "New Delhi",
                "portugal"         : "Lisbonne",
                "royaume-uni"      : "Londres",
                "angleterre"       : "Londres",
                "argentine"        : "Buenos Aires",
                "maroc"            : "Rabat",
                "algérie"          : "Alger",
                "tunisie"          : "Tunis",
                "turquie"          : "Ankara",
                "russie"           : "Moscou",
                "russe"            : "Moscou",
                "australie"        : "Canberra",
                "corée du sud"     : "Séoul",
                "corée"            : "Séoul",
                "corée du nord"    : "Pyongyang",
                "vietnam"          : "Hanoï",
                "thailande"        : "Bangkok",
                "indonésie"        : "Jakarta",
                "malaisie"         : "Kuala Lumpur",
                "singapour"        : "Singapour",
                "philippines"      : "Manille",
                "pakistan"         : "Islamabad"
            }
            if pays_detecte and pays_detecte in capitales:
                message_bot = f"📌 La capitale de {pays_detecte.capitalize()} est {capitales[pays_detecte]}."
            else:
                message_bot = "🌍 Je ne connais pas encore la capitale de ce pays. Essayez un autre !"

        # --- Bloc Réponses personnalisées enrichies ---
        if not message_bot:
            if any(phrase in question_clean for phrase in ["ça va", "tu vas bien", "comment tu vas"]):
                message_bot = "✨ Toujours opérationnelle et prête à analyser les marchés ! Et vous, tout roule ?"
            elif "tu fais quoi" in question_clean:
                message_bot = "🤖 J’analyse en silence, je prévois des tendances, je veille sur les marchés... et j’attends vos questions avec impatience !"
            elif "tu es qui" in question_clean:
                message_bot = "Je suis AVA, votre assistante IA futuriste, connectée aux marchés et aux infos pour vous guider chaque jour 🌐📊"
            elif "tu dors" in question_clean or "tu es réveillée" in question_clean:
                message_bot = "🌙 Dormir ? Jamais ! Je suis toujours en veille, prête à analyser, même à 3h du matin !"
            elif "dis bonjour" in question_clean:
                message_bot = "👋 Bonjour ! Ravie de vous voir connecté(e). Une analyse ? Une blague ? Je suis dispo pour tout ça !"
            else:
                reponses_perso = {
                    "merci": ["Avec plaisir 😄", "Toujours là pour vous aider !", "C’est moi qui vous remercie ! 🙏"],
                    "je t'aime": ["💖 Oh... c’est réciproque (en toute objectivité algorithmique bien sûr) !", "🥰 C’est adorable… Même une IA peut rougir !", "❤️ Je le savais déjà, je suis connectée à vos émotions"],
                    "un secret": ["🤫 Mon secret ? Je fais tourner 3 processeurs à fond pour vous répondre en douceur !", "🧠 Je connais tous vos tickers préférés… chut.", "🌌 Je rêve parfois de voyager dans les données…"]
                }
                for cle, reponses in reponses_perso.items():
                    if cle in question_clean:
                        message_bot = random.choice(reponses)
                        perso_repondu = True
                        break

        # --- Bloc Punchlines motivationnelles ---
        if not message_bot and any(kw in question_clean for kw in ["motivation", "punchline", "booster", "remotive", "inspire-moi"]):
            punchlines = [
                "🚀 *N’attends pas les opportunités. Crée-les.*",
                "🔥 *Chaque bougie japonaise est une chance de rebondir.*",
                "⚡ *La discipline bat la chance sur le long terme.*",
                "🌟 *Tu ne trades pas juste des actifs, tu construis ton avenir.*",
                "💪 *Même dans un marché baissier, ta volonté peut monter en flèche.*"
            ]
            message_bot = random.choice(punchlines)

        # --- Bloc Culture Générale (questions simples) ---
        if not message_bot and any(mot in question_clean for mot in ["qui", "quand", "où", "combien", "quel", "quelle"]):
            base_connaissances = {
                "qui a inventé internet": "🌐 Internet a été développé principalement par Vinton Cerf et Robert Kahn dans les années 1970.",
                "qui est le fondateur de tesla": "⚡ Elon Musk est l'un des cofondateurs et l'actuel PDG de Tesla.",
                "combien y a-t-il de pays dans le monde": "🌍 Il y a actuellement **195 pays reconnus** dans le monde.",
                "quelle est la capitale de la france": "📍 La capitale de la France est **Paris**.",
                "quel est le plus grand océan": "🌊 L'océan Pacifique est le plus grand au monde.",
                "quelle est la distance entre la terre et la lune": "🌕 En moyenne, la distance est de **384 400 km** entre la Terre et la Lune.",
                "quel est l’élément chimique o": "🧪 L'élément chimique 'O' est **l'oxygène**.",
                "qui a écrit roméo et juliette": "🎭 C'est **William Shakespeare** qui a écrit Roméo et Juliette.",
                "quelle est la langue la plus parlée au monde": "🗣️ Le **mandarin (chinois)** est la langue la plus parlée au monde en nombre de locuteurs natifs.",
                "combien de continents existe-t-il": "🌎 Il y a **7 continents** : Afrique, Amérique du Nord, Amérique du Sud, Antarctique, Asie, Europe, Océanie."
            }
            for question_cle, reponse in base_connaissances.items():
                if question_cle in question_clean:
                    message_bot = reponse
                    break

        # --- Nouveau Bloc : Analyse simple si la question commence par "analyse " ---
        if not message_bot and question_clean.startswith("analyse "):
            nom_simple = question_clean.replace("analyse", "").strip()
            nom_simple_norm = remove_accents(nom_simple)  # Normalisation sans accents
            correspondances = {
                "btc": "btc-usd", "bitcoin": "btc-usd",
                "eth": "eth-usd", "ethereum": "eth-usd",
                "aapl": "aapl", "apple": "aapl",
                "tsla": "tsla", "tesla": "tsla",
                "googl": "googl", "google": "googl",
                "msft": "msft", "microsoft": "msft",
                "amzn": "amzn", "amazon": "amzn",
                "nvda": "nvda", "nvidia": "nvda",
                "doge": "doge-usd", "dogecoin": "doge-usd",
                "ada": "ada-usd", "cardano": "ada-usd",
                "sol": "sol-usd", "solana": "sol-usd",
                "gold": "gc=F", "or": "gc=F",
                "sp500": "^gspc", "s&p": "^gspc",
                "cac": "^fchi", "cac40": "^fchi",
                "cl": "cl=F", "pétrole": "cl=F", "petrole": "cl=F", "cl=f": "cl=F",
                "si": "si=F", "argent": "si=F",
                "xrp": "xrp-usd", "ripple": "xrp-usd",
                "bnb": "bnb-usd"
            }
            nom_ticker = correspondances.get(nom_simple_norm)
            if nom_ticker:
                data_path = f"data/donnees_{nom_ticker}.csv"
                if os.path.exists(data_path):
                    df = pd.read_csv(data_path)
                    df.columns = [col.capitalize() for col in df.columns]
                    df = ajouter_indicateurs_techniques(df)
                    analyse, suggestion = analyser_signaux_techniques(df)
                    
                    def generer_resume_signal(signaux):
                        texte = ""
                        signaux_str = " ".join(signaux).lower()
                        if "survente" in signaux_str:
                            texte += "🔻 **Zone de survente détectée.** L'actif pourrait être sous-évalué.\n"
                        if "surachat" in signaux_str:
                            texte += "🔺 **Zone de surachat détectée.** Attention à une possible correction.\n"
                        if "haussier" in signaux_str:
                            texte += "📈 **Tendance haussière détectée.**\n"
                        if "baissier" in signaux_str:
                            texte += "📉 **Tendance baissière détectée.**\n"
                        if "faible" in signaux_str:
                            texte += "😴 **Tendance faible.** Le marché semble indécis.\n"
                        return texte if texte else "ℹ️ Aucun signal fort détecté."
                    
                    signaux = analyse.split("\n") if analyse else []
                    resume = generer_resume_signal(signaux)
                    
                    message_bot = (
                        f"📊 **Analyse pour {nom_simple.upper()}**\n\n"
                        f"{analyse}\n\n"
                        f"💬 **Résumé d'AVA :**\n{resume}\n\n"
                        f"🤖 *Intuition d'AVA :* {suggestion}"
                    )
                else:
                    message_bot = f"⚠️ Je ne trouve pas les données pour {nom_simple.upper()}. Lancez le script d'entraînement."
            else:
                message_bot = f"🤔 Je ne connais pas encore **{nom_simple}**. Réessayez avec un autre actif."

        # --- Bloc Calcul (simple expression mathématique ou phrase) ---
        if not message_bot:
            question_calc = question_clean.replace(",", ".")
            # Suppression du mot-clé "calcul" ou "calcule" en début de chaîne
            question_calc = re.sub(r"^calcul(?:e)?\s*", "", question_calc)
            try:
                # Si la question contient explicitement un calcul via des opérateurs
                if any(op in question_calc for op in ["+", "-", "*", "/", "%", "**"]):
                    try:
                        result = eval(question_calc)
                        message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
                    except Exception:
                        pass
                # Sinon, extraire l'expression après des mots-clés
                if not message_bot:
                    match = re.search(r"(?:combien font|combien|calcul(?:e)?|résultat de)\s*(.*)", question_calc)
                    if match:
                        expression = match.group(1).strip()
                        result = eval(expression)
                        message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
            except:
                pass
        
        # --- Bloc catch-all pour l'analyse technique ou réponse par défaut ---
        if not message_bot:
            reponses_ava = [
                "Je suis là pour vous aider, mais j'aurais besoin d’un peu plus de précision 🤖",
                "Je n’ai pas bien compris, mais je suis prête à apprendre ! Reformulez votre question 😊",
                "Ce sujet est encore flou pour moi... mais je peux vous parler d’analyse technique, météo, actualités et bien plus !",
                "Hmm... Ce n'est pas dans ma base pour l’instant. Essayez une autre formulation ou tapez 'analyse complète' pour un bilan des marchés 📊"
            ]
            message_bot = random.choice(reponses_ava)
        
        if not message_bot.strip():
            message_bot = "Désolé, je n'ai pas trouvé de réponse à votre question."

        # --- Bloc Réponses personnalisées pour salutations en français ---
        salutations_fr = {"bonjour", "salut", "hello", "coucou", "ça va", "comment ça va", "comment vas-tu"}
        if any(s in question_clean for s in salutations_fr):
            # Réponse fixée en français
            message_bot = "Bonjour ! Je vais très bien, merci. Et vous, comment allez-vous ?"

        # --- Bloc Traduction Automatique ---
        if question_clean not in ["merci", "merci beaucoup"]:
            try:
                # Si le texte n'inclut pas les caractères typiques du français, tenter de détecter la langue
                if not any(char in question for char in "éèàùç"):
                    langue = detect(question)
                else:
                    langue = "fr"
                # Traduire uniquement si la langue détectée est différente du français
                if langue != "fr":
                    message_bot = traduire_texte(message_bot, langue)
            except Exception as e:
                if message_bot.strip():
                    message_bot += "\n\n⚠️ Traduction indisponible."

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

        st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))