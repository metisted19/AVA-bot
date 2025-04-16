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
from forex_python.converter import CurrencyRates, CurrencyCodes  # Ces imports peuvent rester si vous en avez besoin pour d'autres parties

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
        api_key = "681120bace124ee99d390cc059e6aca5"
        newsapi = NewsApiClient(api_key=api_key)
        top_headlines = newsapi.get_top_headlines(country="us", page_size=10)
        if not top_headlines:
            return "❌ No data received from NewsAPI. Check your API key and connection."
        articles = top_headlines.get("articles")
        if not articles:
            return "❌ No articles found for this query."
        return [(article["title"], article["url"]) for article in articles if "title" in article and "url" in article]
    except Exception as e:
        return f"❌ Error fetching news via NewsApiClient: {e}"

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
                "remède", "solution naturelle", "astuce maison", "traitement doux", "soulager naturellement",
                "tisane", "huile essentielle", "remedes naturels", "plantes médicinales", "remède maison"
        ]):
            if "stress" in question_clean:
                message_bot = "🧘 Pour le stress : tisane de camomille ou de valériane, respiration profonde, méditation guidée ou bain tiède aux huiles essentielles de lavande."
            elif "mal de gorge" in question_clean or "gorge" in question_clean:
                message_bot = "🍯 Miel et citron dans une infusion chaude, gargarisme d’eau salée tiède, ou infusion de thym. Évite de trop parler et garde ta gorge bien hydratée."
            elif "rhume" in question_clean or "nez bouché" in question_clean:
                message_bot = "🌿 Inhalation de vapeur avec huile essentielle d’eucalyptus, tisane de gingembre, et bouillon chaud. Repose-toi bien."
            elif "fièvre" in question_clean:
                message_bot = "🧊 Infusion de saule blanc, cataplasme de vinaigre de cidre sur le front, linge froid sur les poignets et repos absolu."
            elif "digestion" in question_clean or "ventre" in question_clean:
                message_bot = "🍵 Infusion de menthe poivrée ou fenouil, massage abdominal doux dans le sens des aiguilles d’une montre, alimentation légère."
            elif "toux" in question_clean:
                message_bot = "🌰 Sirop naturel à base d’oignon et miel, infusion de thym, ou inhalation de vapeur chaude. Évite les environnements secs."
            elif "insomnie" in question_clean or "sommeil" in question_clean:
                message_bot = "🌙 Tisane de passiflore, valériane ou verveine. Évite les écrans avant le coucher, opte pour une routine calme et tamise la lumière."
            elif "brûlure d'estomac" in question_clean or "reflux" in question_clean:
                message_bot = "🔥 Une cuillère de gel d’aloe vera, infusion de camomille ou racine de guimauve. Évite les repas copieux et mange lentement."
            elif "peau" in question_clean or "acné" in question_clean:
                message_bot = "🧼 Masque au miel et curcuma, infusion de bardane, et hydratation régulière. Évite les produits agressifs."
            elif "fatigue" in question_clean:
                message_bot = "⚡ Cure de gelée royale, infusion de ginseng ou d’éleuthérocoque, alimentation riche en fruits et repos régulier."
            elif "maux de tête" in question_clean or "migraine" in question_clean:
                message_bot = "🧠 Huile essentielle de menthe poivrée sur les tempes, infusion de grande camomille ou compresse froide sur le front."
            elif "nausée" in question_clean:
                message_bot = "🍋 Un peu de gingembre frais râpé, infusion de menthe douce ou respiration lente en position semi-allongée."
            elif "crampes" in question_clean:
                message_bot = "🦵 Eau citronnée, étirements doux, magnésium naturel via les graines, amandes ou bananes."
            else:
                message_bot = "🌱 Je connais plein de remèdes naturels ! Dites-moi pour quel symptôme ou souci, et je vous propose une solution douce et efficace."

        # --- Bloc Réponses médicales explicites ---
        elif not message_bot and any(mot in question_clean for mot in [ "grippe", "rhume", "fièvre", "migraine", "angine", "hypertension", "stress", "toux", "maux", "douleur", "asthme", "bronchite",
            "eczéma", "diabète", "cholestérol", "acné", "ulcère", "anémie", "insomnie", "vertige", "brûlures", "reflux", "nausée", "dépression",
            "allergie", "palpitations", "otite", "sinusite", "crampes", "infections urinaires", "fatigue", "constipation", "diarrhée",
            "ballonnements", "brûlures d’estomac", "brûlure d'estomac", "saignement de nez", "mal de dos", "entorse", "tendinite",
            "ampoule", "piqûre d’insecte", "bruit dans l'oreille", "angoisse", "boutons de fièvre", "lombalgie", "périarthrite", "hallux valgus",
            "hallucinations", "trouble du sommeil", "inflammation", "baisse de tension", "fièvre nocturne"
            ]):
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
                "ulcère": "🩻 Les ulcères nécessitent un suivi médical attentif, une modification de l'alimentation et parfois des traitements médicamenteux spécifiques.",
                "anémie": "🩸 Fatigue, pâleur, essoufflement. Manque de fer ? Misez sur viande rouge, lentilles, épinards !",
                "insomnie": "🌙 Difficultés à dormir ? Évitez les écrans avant le coucher, créez une routine apaisante.",
                "vertige": "🌀 Perte d’équilibre, nausée ? Cela peut venir des oreilles internes. Reposez-vous et évitez les mouvements brusques.",
                "brûlures": "🔥 Refroidissez rapidement la zone (eau tiède, jamais glacée), puis appliquez une crème apaisante.",
                "reflux": "🥴 Brûlures d’estomac ? Évitez les repas copieux, le café et dormez la tête surélevée.",
                "nausée": "🤢 Boissons fraîches, gingembre ou citron peuvent apaiser. Attention si vomissements répétés.",
                "dépression": "🖤 Fatigue, repli, tristesse persistante ? Parlez-en. Vous n’êtes pas seul(e), des aides existent.",
                "allergie": "🤧 Éternuements, démangeaisons, yeux rouges ? Pollen, acariens ou poils ? Antihistaminiques peuvent aider.",
                "palpitations": "💓 Sensation de cœur qui s’emballe ? Cela peut être bénin, mais consultez si cela se répète.",
                "otite": "👂 Douleur vive à l’oreille, fièvre ? Surtout chez les enfants. Consultez sans tarder.",
                "sinusite": "👃 Pression au visage, nez bouché, fièvre ? Hydratez-vous, faites un lavage nasal, et consultez si nécessaire.",
                "crampes": "💥 Hydratez-vous, étirez les muscles concernés. Magnésium ou potassium peuvent aider.",
                "infections urinaires": "🚽 Brûlures en urinant, besoin fréquent ? Buvez beaucoup d’eau et consultez rapidement.",
                "fatigue": "😴 Fatigue persistante ? Sommeil insuffisant, stress ou carences. Écoutez votre corps, reposez-vous.",
                "constipation": "🚽 Alimentation riche en fibres, hydratation et activité physique peuvent soulager naturellement.",
                "diarrhée": "💧 Boire beaucoup d’eau, manger du riz ou des bananes. Attention si cela persiste plus de 2 jours.",
                "ballonnements": "🌬️ Évitez les boissons gazeuses, mangez lentement, privilégiez les aliments faciles à digérer.",
                "brûlures d’estomac": "🔥 Surélevez votre tête la nuit, évitez les plats gras ou épicés. Un antiacide peut aider.",
                "saignement de nez": "🩸 Penchez la tête en avant, pincez le nez 10 minutes. Si répétitif, consultez.",
                "mal de dos": "💺 Mauvaise posture ? Étirements doux, repos et parfois un coussin lombaire peuvent soulager.",
                "entorse": "🦶 Glace, repos, compression, élévation (méthode GREC). Consultez si douleur intense.",
                "tendinite": "💪 Repos de la zone, glace et mouvements doux. Évitez les efforts répétitifs.",
                "ampoule": "🦶 Ne percez pas. Nettoyez doucement, couvrez avec un pansement stérile.",
                "piqûre d’insecte": "🦟 Rougeur, démangeaison ? Lavez à l’eau et au savon, appliquez un gel apaisant.",
                "bruit dans l'oreille": "🎧 Acouphène ? Bruit persistant dans l’oreille. Repos auditif, réduction du stress, consultez si persistant.",
                "angoisse": "🧘‍♂️ Respiration profonde, exercices de pleine conscience, écoutez votre corps. Parlez-en si nécessaire.",
                "boutons de fièvre": "👄 Herpès labial ? Évitez le contact, appliquez une crème spécifique dès les premiers signes.",
                "lombalgie": "🧍‍♂️ Douleur en bas du dos ? Évitez les charges lourdes, dormez sur une surface ferme.",
                "périarthrite": "🦴 Inflammation autour d’une articulation. Froid local, repos, et anti-inflammatoires si besoin.",
                "hallux valgus": "👣 Déformation du gros orteil ? Port de chaussures larges, semelles spéciales ou chirurgie selon le cas."
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
                    "pakistan"         : "Islamabad",
                    "bangladesh"       : "Dacca",
                    "sri lanka"        : "Colombo",
                    "népal"            : "Katmandou",
                    "iran"             : "Téhéran",
                    "irak"             : "Bagdad",
                    "syrie"            : "Damas",
                    "liban"            : "Beyrouth",
                    "jordanie"         : "Amman",
                    "israël"           : "Jérusalem",
                    "palestine"        : "Ramallah",
                    "qatar"            : "Doha",
                    "oman"             : "Mascate",
                    "yémen"            : "Sanaa",
                    "afghanistan"      : "Kaboul",
                    "émirats arabes unis" : "Abou Dabi",
                    "sénégal"          : "Dakar",
                    "côte d'ivoire"    : "Yamoussoukro",
                    "mali"             : "Bamako",
                    "niger"            : "Niamey",
                    "tchad"            : "N'Djaména",
                    "burkina faso"     : "Ouagadougou",
                    "congo"            : "Brazzaville",
                    "rd congo"         : "Kinshasa",
                    "kenya"            : "Nairobi",
                    "éthiopie"         : "Addis-Abeba",
                    "ghana"            : "Accra",
                    "zambie"           : "Lusaka",
                    "zimbabwe"         : "Harare",
                    "soudan"           : "Khartoum",
                    "botswana"         : "Gaborone",
                    "namibie"          : "Windhoek",
                    "madagascar"       : "Antananarivo",
                    "mozambique"       : "Maputo",
                    "angola"           : "Luanda",
                    "libye"            : "Tripoli",
                    "egypte"           : "Le Caire",
                    "grèce"            : "Athènes",
                    "pologne"          : "Varsovie",
                    "ukraine"          : "Kyiv",
                    "roumanie"         : "Bucarest",
                    "bulgarie"         : "Sofia",
                    "serbie"           : "Belgrade",
                    "croatie"          : "Zagreb",
                    "slovénie"         : "Ljubljana",
                    "hongrie"          : "Budapest",
                    "tchéquie"         : "Prague",
                    "slovaquie"        : "Bratislava",
                    "suède"            : "Stockholm",
                    "norvège"          : "Oslo",
                    "finlande"         : "Helsinki",
                    "islande"          : "Reykjavik",
                    "belgique"         : "Bruxelles",
                    "pays-bas"         : "Amsterdam",
                    "irlande"          : "Dublin",
                    "suisse"           : "Berne",
                    "colombie"         : "Bogota",
                    "pérou"            : "Lima",
                    "chili"            : "Santiago",
                    "équateur"         : "Quito",
                    "uruguay"          : "Montevideo",
                    "paraguay"         : "Asuncion",
                    "bolivie"          : "Sucre",
                    "venezuela"        : "Caracas",
                    "cuba"             : "La Havane",
                    "haïti"            : "Port-au-Prince",
                    "république dominicaine" : "Saint-Domingue"
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
                    "qui a inventé internet": "🌐 Internet a été développé principalement par **Vinton Cerf** et **Robert Kahn** dans les années 1970.",
                    "qui est le fondateur de tesla": "⚡ Elon Musk est l'un des cofondateurs et l'actuel PDG de **Tesla**.",
                    "combien y a-t-il de pays dans le monde": "🌍 Il y a actuellement **195 pays reconnus** dans le monde.",
                    "quelle est la capitale de la france": "📍 La capitale de la France est **Paris**.",
                    "quel est le plus grand océan": "🌊 L'océan Pacifique est le plus grand au monde.",
                    "quelle est la distance entre la terre et la lune": "🌕 En moyenne, la distance est de **384 400 km** entre la Terre et la Lune.",
                    "quel est l’élément chimique o": "🧪 L'élément chimique 'O' est **l'oxygène**.",
                    "qui a écrit roméo et juliette": "🎭 C'est **William Shakespeare** qui a écrit *Roméo et Juliette*.",
                    "quelle est la langue la plus parlée au monde": "🗣️ Le **mandarin** est la langue la plus parlée au monde en nombre de locuteurs natifs.",
                    "combien de continents existe-t-il": "🌎 Il y a **7 continents** : Afrique, Amérique du Nord, Amérique du Sud, Antarctique, Asie, Europe, Océanie.",
                    "qui a marché sur la lune en premier": "👨‍🚀 **Neil Armstrong** a été le premier homme à marcher sur la Lune en 1969.",
                    "quelle est la plus haute montagne du monde": "🏔️ L’**Everest** est la plus haute montagne du monde, culminant à 8 848 mètres.",
                    "combien y a-t-il d’os dans le corps humain": "🦴 Le corps humain adulte compte **206 os**.",
                    "qui a peint la joconde": "🖼️ C’est **Léonard de Vinci** qui a peint *La Joconde*.",
                    "quelle est la capitale du japon": "🏙️ La capitale du Japon est **Tokyo**.",
                    "quelle planète est la plus proche du soleil": "☀️ **Mercure** est la planète la plus proche du Soleil.",
                    "qui a inventé l’électricité": "⚡ L'électricité n’a pas été inventée, mais **Benjamin Franklin** et **Thomas Edison** ont été des figures clés dans sa compréhension et son exploitation.",
                    "qu’est-ce que l’adn": "🧬 L’**ADN** est le support de l’information génétique chez tous les êtres vivants.",
                    "quelle est la plus grande forêt du monde": "🌳 L’**Amazonie** est la plus grande forêt tropicale du monde.",
                    "quel est l’animal terrestre le plus rapide": "🐆 Le **guépard** peut atteindre jusqu’à 110 km/h en vitesse de pointe.",
                    "qui a écrit harry potter": "📚 C’est **J.K. Rowling** qui a écrit la saga *Harry Potter*.",
                    "quelle est la température de l’eau qui bout": "💧 L’eau bout à **100°C** à pression atmosphérique normale.",
                    "quel est le pays le plus peuplé": "👥 **La Chine** est actuellement le pays le plus peuplé du monde.",
                    "quel est le plus long fleuve du monde": "🌊 Le **Nil** est souvent considéré comme le plus long fleuve du monde, bien que certains estiment que c’est l’Amazone."
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
                "bnb": "bnb-usd",
                "matic": "matic-usd", "polygon": "matic-usd",
                "uni": "uni-usd", "uniswap": "uni-usd",
                "ndx": "^ndx", "nasdaq": "^ndx", "nasdaq100": "^ndx"
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
            question_calc = re.sub(r"^calcul(?:e)?\s*", "", question_calc)
            try:
                if any(op in question_calc for op in ["+", "-", "*", "/", "%", "**"]):
                    try:
                        result = eval(question_calc)
                        message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
                    except Exception:
                        pass
                if not message_bot:
                    match = re.search(r"(?:combien font|combien|calcul(?:e)?|résultat de)\s*(.*)", question_calc)
                    if match:
                        expression = match.group(1).strip()
                        result = eval(expression)
                        message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
            except:
                pass

        # --- Bloc Convertisseur intelligent ---
        if not message_bot and any(kw in question_clean for kw in ["convertis", "convertir", "combien vaut", "en dollars", "en euros", "en km", "en miles", "en mètres", "en celsius", "en fahrenheit"]):
            try:
                phrase = question_clean.replace(",", ".")
                match = re.search(r"(\d+(\.\d+)?)\s*([a-z]{3})\s*(en|to)\s*([a-z]{3})", phrase, re.IGNORECASE)
                if match:
                    montant = float(match.group(1))
                    from_cur = match.group(3).upper()
                    to_cur = match.group(5).upper()
                    url = f"https://v6.exchangerate-api.com/v6/dab2bba4f43a99445158d9ae/latest/{from_cur}"
                    response = requests.get(url, timeout=10)
                    data = response.json()
                    if data.get("result") == "success":
                        taux = data["conversion_rates"].get(to_cur)
                        if taux:
                            result = montant * taux
                            message_bot = f"💱 {montant} {from_cur} = {round(result, 2)} {to_cur}"
                        else:
                            message_bot = "❌ Taux de conversion non disponible pour la devise demandée."
                    else:
                        message_bot = "⚠️ Désolé, la conversion n’a pas pu être effectuée en raison d’un problème avec l’API. Veuillez réessayer plus tard."
                elif "km en miles" in phrase:
                    match = re.search(r"(\d+(\.\d+)?)\s*km", phrase)
                    if match:
                        km = float(match.group(1))
                        miles = km * 0.621371
                        message_bot = f"📏 {km} km = {round(miles, 2)} miles"
                elif "miles en km" in phrase:
                    match = re.search(r"(\d+(\.\d+)?)\s*miles?", phrase)
                    if match:
                        mi = float(match.group(1))
                        km = mi / 0.621371
                        message_bot = f"📏 {mi} miles = {round(km, 2)} km"
                elif "celsius en fahrenheit" in phrase:
                    match = re.search(r"(\d+(\.\d+)?)\s*c", phrase)
                    if match:
                        celsius = float(match.group(1))
                        fahrenheit = (celsius * 9/5) + 32
                        message_bot = f"🌡️ {celsius}°C = {round(fahrenheit, 2)}°F"
                elif "fahrenheit en celsius" in phrase:
                    match = re.search(r"(\d+(\.\d+)?)\s*f", phrase)
                    if match:
                        f_temp = float(match.group(1))
                        c_temp = (f_temp - 32) * 5/9
                        message_bot = f"🌡️ {f_temp}°F = {round(c_temp, 2)}°C"
            except Exception as e:
                message_bot = f"⚠️ Désolé, la conversion n’a pas pu être effectuée en raison d’un problème de connexion. Veuillez réessayer plus tard."

        # === Bloc Reconnaissance des tickers (exemple) ===
        if any(symb in question_clean for symb in ["btc", "bitcoin", "eth", "ethereum", "aapl", "apple", "tsla", "tesla", "googl", "google", "msft", "microsoft", "amzn", "amazon", "nvda", "nvidia", "doge", "dogecoin", "ada", "cardano", "sol", "solana", "gold", "or", "sp500", "s&p", "cac", "cac40", "cl", "petrole", "pétrole", "si", "argent", "xrp", "ripple", "bnb", "matic", "polygon", "uni", "uniswap", "ndx", "nasdaq", "nasdaq100"]):
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
                nom_ticker = "^gspc"
            elif "doge" in nom_ticker or "dogecoin" in nom_ticker:
                nom_ticker = "doge-usd"
            elif "ada" in nom_ticker or "cardano" in nom_ticker:
                nom_ticker = "ada-usd"
            elif "sol" in nom_ticker or "solana" in nom_ticker:
                nom_ticker = "sol-usd"
            elif "gold" in nom_ticker or "or" in nom_ticker:
                nom_ticker = "gc=F"
            elif "xrp" in nom_ticker or "ripple" in nom_ticker:
                nom_ticker = "xrp-usd"
            elif "bnb" in nom_ticker:
                nom_ticker = "bnb-usd"
            elif "cl" in nom_ticker or "petrole" in nom_ticker or "pétrole" in nom_ticker:
                nom_ticker = "cl=F"
            elif "si" in nom_ticker or "argent" in nom_ticker:
                nom_ticker = "si=F"
            elif "matic" in nom_ticker or "polygon" in nom_ticker:
                nom_ticker = "matic-usd"
            elif "uni" in nom_ticker or "uniswap" in nom_ticker:
                nom_ticker = "uni-usd"
            elif "ndx" in nom_ticker or "nasdaq" in nom_ticker or "nasdaq100" in nom_ticker:
                nom_ticker = "^ndx"
        
        # --- Bloc Salutations Simples ---
        if not message_bot and any(mot in question_clean for mot in ["salut", "bonjour", "bonsoir", "yo", "coucou", "hey"]):
            reponses_salut = [
                "👾 Hey ! Moi c’est AVA, votre copilote futuriste.",
                "🎯 Toujours connectée ! Que puis-je faire pour vous ?",
                "🧠 Présente et prête à analyser les signaux !",
                "😎 Yo ! Prêt pour une session d’analyse ou un peu de culture ?"
            ]
            message_bot = random.choice(reponses_salut)
        
        # --- Bloc Quiz de culture générale ---
        if not message_bot and any(mot in question_clean for mot in [
            "quiz", "quizz", "question", "culture générale", "pose-moi une question", "teste mes connaissances"
        ]):
            quizz_culture = [
                {"question": "🌍 Quelle est la capitale de l'Australie ?", "réponse": "canberra"},
                {"question": "🧪 Quel est l'élément chimique dont le symbole est O ?", "réponse": "oxygène"},
                {"question": "🖼️ Qui a peint la Joconde ?", "réponse": "léonard de vinci"},
                {"question": "📚 Combien y a-t-il de continents sur Terre ?", "réponse": "7"},
                {"question": "🚀 Quelle planète est la plus proche du Soleil ?", "réponse": "mercure"},
                {"question": "🇫🇷 Qui a écrit 'Les Misérables' ?", "réponse": "victor hugo"},
                {"question": "🎬 Quel film a remporté l'Oscar du meilleur film en 1998 avec 'Titanic' ?", "réponse": "titanic"},
                {"question": "🐘 Quel est le plus grand animal terrestre ?", "réponse": "éléphant"},
                {"question": "🎼 Quel musicien est surnommé 'le Roi de la Pop' ?", "réponse": "michael jackson"},
                {"question": "⚽ Quelle nation a remporté la Coupe du Monde 2018 ?", "réponse": "france"}
            ]
            question_choisie = random.choice(quizz_culture)
            st.session_state["quiz_attendu"] = question_choisie["réponse"].lower()
            message_bot = f"🧠 **Quiz Culture G** :\n{question_choisie['question']}\n\nRépondez directement !"

        # --- Vérification de la réponse au quiz ---
        elif "quiz_attendu" in st.session_state and st.session_state["quiz_attendu"]:
            reponse_attendue = st.session_state["quiz_attendu"]
            if question_clean.lower() == reponse_attendue:
                message_bot = "✅ Bonne réponse ! Vous avez l’esprit affûté 🧠💪"
            else:
                message_bot = f"❌ Oops ! Ce n'était pas ça... La bonne réponse était **{reponse_attendue.capitalize()}**."
            st.session_state["quiz_attendu"] = ""
        # --- Bloc Faits Insolites ---
        # À insérer juste avant le bloc catch-all final
        if not message_bot and any(mot in question_clean for mot in ["fait insolite", "truc fou", "surprends-moi", "anecdote", "incroyable mais vrai"]):
            faits_insolites = [
                "🐙 Un poulpe a trois cœurs… et son sang est bleu !",
                "🚽 Plus de gens possèdent un téléphone portable qu’une brosse à dents.",
                "🐌 Un escargot peut dormir pendant trois ans d’affilée.",
                "🌋 Il y a plus de volcans sous l’eau que sur la terre ferme.",
                "📦 Amazon a été fondée dans un garage... et maintenant, ils livrent même des frigos !",
                "🧠 Le cerveau humain génère assez d’électricité pour allumer une petite ampoule.",
                "🌕 On a découvert de la glace sur la Lune, et même des poches d’eau sur Mars !",
                "🔋 Un éclair contient assez d'énergie pour faire griller 100 000 toasts.",
                "🕷️ Certaines araignées peuvent planer dans les airs à l’aide de fils de soie… c’est le *ballooning* !",
                "🦑 Le calmar géant a les plus grands yeux du règne animal, aussi gros qu’un ballon de foot !"
            ]
            message_bot = random.choice(faits_insolites)
        # --- Bloc Recettes rapides ---
        elif any(mot in question_clean for mot in ["recette", "cuisine", "plat rapide", "idée repas", "je mange quoi"]):
            recettes = [
                "🥪 **Sandwich thon-avocat** : pain complet, thon, avocat écrasé, citron, sel, poivre. 5 minutes chrono !",
                "🍝 **Pâtes à l’ail** : pâtes + ail émincé + huile d’olive + herbes. Simple, rapide, efficace.",
                "🍳 **Omelette fromage** : œufs battus, sel, poivre, fromage râpé. 5 minutes à la poêle !",
                "🥗 **Salade express** : tomates cerises, mozzarella, roquette, huile d’olive, vinaigre balsamique.",
                "🌯 **Wrap poulet-crudités** : galette + restes de poulet + salade + sauce yaourt.",
                "🥔 **Pommes de terre sautées** : en cubes, à la poêle avec ail et persil. Parfait avec des œufs !",
                "🍲 **Soupe express** : légumes surgelés mixés + cube bouillon + crème légère. Prête en 10 minutes."
            ]
            message_bot = f"🍽️ Une petite faim ? Voici une idée :\n\n{random.choice(recettes)}"

        # --- Bloc Mini base générale (culture quotidienne) ---
        if not message_bot:
            base_generale = {
                base_generale = {
                    # 🌍 Météo & nature
                    "quelle est la température idéale pour un être humain": "🌡️ La température corporelle idéale est autour de 36,5 à 37°C.",
                    "qu'est-ce qu'un ouragan": "🌀 Un ouragan est une tempête tropicale très puissante, formée au-dessus des océans chauds.",
                    "comment se forme un arc-en-ciel": "🌈 Un arc-en-ciel se forme par la réfraction, la réflexion et la dispersion de la lumière dans les gouttelettes d'eau.",
    
                    # 🐾 Animaux
                    "combien de cœurs a une pieuvre": "🐙 Une pieuvre a **trois cœurs** ! Deux pour les branchies et un pour le corps.",
                    "quel est l’animal le plus rapide du monde": "🐆 Le guépard est l’animal terrestre le plus rapide, avec une pointe à 112 km/h.",
                    "quel animal pond des œufs mais allaite": "🦘 L’ornithorynque ! Un mammifère unique qui pond des œufs et allaite ses petits.",
    
                    # 🔬 Science
                    "qu'est-ce que la gravité": "🌌 La gravité est une force qui attire deux masses l'une vers l'autre, comme la Terre attire les objets vers elle.",
                    "combien de planètes dans le système solaire": "🪐 Il y a 8 planètes : Mercure, Vénus, Terre, Mars, Jupiter, Saturne, Uranus, Neptune.",
                    "quelle est la plus petite particule": "⚛️ Le quark est l'une des plus petites particules connues dans la physique quantique.",
    
                    # 📚 Histoire
                    "qui était napoléon": "👑 Napoléon Bonaparte était un empereur français du XIXe siècle, célèbre pour ses conquêtes militaires.",
                    "en quelle année la tour eiffel a été construite": "🗼 Elle a été achevée en **1889** pour l'Exposition universelle de Paris.",
                    "quelle guerre a eu lieu en 1914": "⚔️ La Première Guerre mondiale a commencé en 1914 et s'est terminée en 1918.",
    
                    # 🧠 Connaissances générales
                    "quelle est la langue officielle du brésil": "🇧🇷 C’est le **portugais**.",
                    "combien de dents a un adulte": "🦷 Un adulte possède généralement **32 dents**.",
                    "qu'est-ce que le code morse": "📡 C’est un système de communication utilisant des points et des tirets.",
    
                    # 🧮 Maths & Logique
                    "quelle est la racine carrée de 144": "🧮 La racine carrée de 144 est **12**.",
                    "combien font 12 fois 8": "📊 12 multiplié par 8 égale **96**.",
    
                    # 🗺️ Géographie bonus
                    "quel est le plus long fleuve du monde": "🌊 Le Nil et l’Amazone se disputent le titre, mais l’Amazone est souvent considéré comme le plus long.",
                    "quel est le pays le plus peuplé": "👥 La Chine est le pays le plus peuplé, avec plus d’1,4 milliard d’habitants.",
    
                    # ⏰ Temps & Calendrier
                     "combien y a-t-il de jours dans une année": "📅 Une année classique compte **365 jours**, et **366** lors des années bissextiles.",
                    "quels sont les mois de l'été": "☀️ En France, l'été comprend **juin, juillet et août**."
                }

            }

            for question_base, reponse_base in base_generale.items():
                if question_base in question_clean:
                    message_bot = reponse_base
                    break

        # --- Bloc catch-all pour l'analyse technique ou réponse par défaut ---
        if not message_bot:
            if any(phrase in question_clean for phrase in ["hello", "hi", "good morning", "good afternoon", "good evening"]):
                message_bot = "Hello! I'm here and ready to help. How can I assist you today?"
            else:
                reponses_ava = [
                    "I'm here to help, but I need a bit more detail 🤖",
                    "I didn't quite understand that; could you please rephrase?",
                    "This subject is still a bit unclear to me... I can talk about technical analysis, weather, news, and much more!",
                    "Hmm... That's not in my database yet. Try another phrasing or type 'complete analysis' for a market overview 📊"
                ]
                message_bot = random.choice(reponses_ava)


    # --- Bloc Traduction corrigé ---
        def traduire_deepl(texte, langue_cible="EN", api_key="0f57cbca-eac1-4c8a-b809-11403947afe4:fx"):
            url = "https://api-free.deepl.com/v2/translate"
            params = {
                "auth_key": api_key,
                "text": texte,
                "target_lang": langue_cible
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            # Détecter la langue de la question et loguer le résultat
            try:
                lang_question = detect(question)
            except Exception as e:
                lang_question = "fr"
            if lang_question.lower() != "fr" and message_bot.strip():
                traduction = traduire_deepl(message_bot, langue_cible=lang_question.upper())
                message_bot = traduction
            
        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})
        st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))

