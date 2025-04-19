import streamlit as st
import os
import re
import random
from datetime import datetime
import pandas as pd
import requests
from PIL import Image
from langdetect import detect
from newsapi import NewsApiClient
from forex_python.converter import CurrencyRates, CurrencyCodes
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_meteo import obtenir_meteo, get_meteo_ville  
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity 
import unicodedata, re
import difflib
from fonctions_chat import obtenir_reponse_ava 
import urllib.parse
import glob
import json
from typing import Optional

# 1️⃣ Configuration de la page (toujours juste après les imports)
st.set_page_config(page_title="Chat AVA", layout="centered")

# 2️⃣ Définition du dossier courant
SCRIPT_DIR = os.path.dirname(__file__)

def ajuster_affection(question):
    style = charger_style_ava()
    affection = style.get("niveau_affection", 0.5)

    question = question.lower()

    # Mots doux = elle s’attache
    mots_gentils = ["merci", "tu es géniale", "bravo", "je t’aime", "trop forte", "tu assures", "t’es incroyable"]
    # Mots durs = elle se referme
    mots_durs = ["t’es nulle", "aucune utilité", "tu sers à rien", "c’est nul", "je te déteste", "ta gueule"]

    if any(mot in question for mot in mots_gentils):
        affection = min(1.0, affection + 0.05)
    elif any(mot in question for mot in mots_durs):
        affection = max(0.0, affection - 0.05)

    style["niveau_affection"] = round(affection, 2)
    sauvegarder_style_ava(style)

def incrementer_interactions():
    style = charger_style_ava()
    style["compteur_interactions"] = style.get("compteur_interactions", 0) + 1

    # Bonus : elle évolue tous les 20 messages
    if style["compteur_interactions"] % 20 == 0:
        style["niveau_spontane"] = min(style["niveau_spontane"] + 0.05, 1.0)
        style["niveau_humour"] = min(style["niveau_humour"] + 0.05, 1.0)
        style["niveau_libre_arbitre"] = min(style["niveau_libre_arbitre"] + 0.03, 1.0)

    sauvegarder_style_ava(style)

def charger_style_ava():
    try:
        with open("style_ava.json", "r") as f:
            return json.load(f)
    except:
        return {
            "ton": "neutre",
            "langage": "classique",
            "niveau_humour": 0.3,
            "niveau_spontane": 0.3,
            "niveau_libre_arbitre": 0.3,
            "compteur_interactions": 0,
            "niveau_affection": 0.5
        }

def sauvegarder_style_ava(style):
    with open("style_ava.json", "w") as f:
        json.dump(style, f, indent=4)

        
# 2️⃣ Dossier courant
SCRIPT_DIR = os.path.dirname(__file__)
# 3️⃣ Chargement de la base de connaissances
FICHIER_BASE = os.path.join(SCRIPT_DIR, "base_connaissances.json")
try:
    with open(FICHIER_BASE, "r", encoding="utf-8") as f:
        base_savoir = json.load(f)
except Exception as e:
    st.error(f"Impossible de charger base_connaissances.json : {e}")
    base_savoir = {}

# 3️⃣ Identification de l’utilisateur
if "user_id" not in st.session_state:
    pseudo = st.text_input("🔑 Entrez votre pseudo pour commencer :", key="login_input")
    if not pseudo:
        st.stop()
    st.session_state["user_id"] = pseudo.strip()
user = st.session_state["user_id"]

# 4️⃣ Chemins vers les fichiers de mémoire
GLOBAL_MEMOIRE = os.path.join(SCRIPT_DIR, "memoire_ava.json")                         # ta base « gingembre »…
USER_MEMOIRE   = os.path.join(SCRIPT_DIR, f"memoire_ava_{user}.json")                # version perso
PROFIL_FILE    = os.path.join(SCRIPT_DIR, f"profil_utilisateur_{user}.json")         # prénom, goûts, etc.

# 5️⃣ Chargement des souvenirs dynamiques
if "souvenirs" not in st.session_state:
    try:
        # 5.a) on tente le fichier user
        with open(USER_MEMOIRE, "r", encoding="utf-8") as f:
            st.session_state["souvenirs"] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 5.b) fallback sur le global
        try:
            with open(GLOBAL_MEMOIRE, "r", encoding="utf-8") as f:
                st.session_state["souvenirs"] = json.load(f)
        except:
            st.session_state["souvenirs"] = {}
        # on copie immédiatement dans le fichier user pour qu’il persiste
        with open(USER_MEMOIRE, "w", encoding="utf-8") as f:
            json.dump(st.session_state["souvenirs"], f, ensure_ascii=False, indent=2)

def _save_souvenirs():
    with open(USER_MEMOIRE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["souvenirs"], f, ensure_ascii=False, indent=2)

def stocker_souvenir(cle: str, valeur: str):
    st.session_state["souvenirs"][cle] = valeur
    _save_souvenirs()

def retrouver_souvenir(cle: str) -> str:
    return st.session_state["souvenirs"].get(
        cle,
        "❓ Je n'ai pas de souvenir pour ça… Peux‑tu me le redire ?"
    )

# 6️⃣ Chargement du profil utilisateur (prénom, etc.)
if "profil" not in st.session_state:
    try:
        with open(PROFIL_FILE, "r", encoding="utf-8") as f:
            st.session_state["profil"] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state["profil"] = {}

def _save_profil():
    with open(PROFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["profil"], f, ensure_ascii=False, indent=2)

def stocker_profil(cle: str, valeur: str):
    st.session_state["profil"][cle] = valeur
    _save_profil()

def retrouver_profil(cle: str):
    return st.session_state["profil"].get(cle, None)
# ───────────────────────────────────────────────────────────────────────

# --- Modèle sémantique (cache) ---
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")
model_semantic = load_model()

# --- Nettoyage du texte ---
def nettoyer_texte(txt):
    txt = unicodedata.normalize("NFKC", txt)
    txt = txt.replace("’", "'")
    txt = txt.lower().strip()
    txt = re.sub(r"[^\w\sàâäéèêëïîôöùûüç]", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt

# Fonction pour supprimer les accents d'une chaîne de caractères
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


API_KEY = "3b2ff0b77dd65559ba4a1a69769221d5"

def geocode_location(lieu):
    """Retourne (lat, lon) via le geocoding OWM, ou (None, None)."""
    q = urllib.parse.quote(remove_accents(lieu))
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={q}&limit=1&appid={API_KEY}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200 and resp.json():
        data = resp.json()[0]
        return data["lat"], data["lon"]
    return None, None

def get_meteo_ville(city):
    """1) Géocode 2) Récupère la météo par lat/lon, 3) fallback sur city brut."""
    lat, lon = geocode_location(city)
    if lat is not None and lon is not None:
        url = (
            f"http://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fr"
        )
    else:
        # fallback : requête par nom
        url = (
            f"http://api.openweathermap.org/data/2.5/weather?"
            f"q={urllib.parse.quote(city)}&appid={API_KEY}&units=metric&lang=fr"
        )

    resp = requests.get(url, timeout=5)
    if resp.status_code != 200:
        return "Erreur: données météo non disponibles."

    data = resp.json()
    desc = data["weather"][0]["description"].capitalize()
    temp = data["main"]["temp"]
    hum  = data["main"].get("humidity", "N/A")
    vent = data["wind"].get("speed", "N/A")
    return f"{desc} avec {temp}°C, humidité : {hum}%, vent : {vent} m/s."
# --- Bloc Traduction corrigé ---
def traduire_deepl(texte, langue_cible="EN", api_key="0f57cbca-eac1-4c8a-b809-11403947afe4:fx"):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": api_key,
        "text": texte,
        "target_lang": langue_cible
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

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
def style_reponse_ava(texte):
    style = charger_style_ava()
    humour = style.get("niveau_humour", 0.5)
    spontane = style.get("niveau_spontane", 0.5)
    ton = style.get("ton", "neutre")
    affection = style.get("niveau_affection", 0.5)

    if random.random() < humour:
        texte += " 😏 (Trop facile pour moi.)"

    if random.random() < spontane:
        texte += " Et j’te balance ça comme une ninja de l’info."

    if affection > 0.8:
        texte = "💙 " + texte + " J’adore nos discussions."
    elif affection < 0.3:
        texte = "😐 " + texte + " (Mais je vais pas faire d’effort si tu continues comme ça...)"
    elif ton == "malicieuse":
        texte = "Hmm... " + texte
    elif ton == "sérieuse":
        texte = "[Réponse sérieuse] " + texte

    return texte


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



def trouver_reponse(question: str) -> str:
    question_clean = nettoyer_texte(question)

    incrementer_interactions()  # 🔁 AVA évolue à chaque interaction ici
    ajuster_affection(question)
    

    # 1) Modules spéciaux (on passe bien les DEUX arguments)
    reponse = gerer_modules_speciaux(question, question_clean)
    if reponse:
        return reponse

    # 2) Recherche directe
    if question_clean in base_complet:
        return base_complet[question_clean]

    # 3) Fuzzy
    proche = difflib.get_close_matches(question_clean, base_complet.keys(), n=1, cutoff=0.85)
    if proche:
        return base_complet[proche[0]]

    # 4) Sémantique
    keys = list(base_complet.keys())
    vb   = model_semantic.encode(keys)
    vq   = model_semantic.encode([question_clean])[0]
    sims = cosine_similarity([vq], vb)[0]
    best, score = max(zip(keys, sims), key=lambda x: x[1])
    if score > 0.7:
        return base_complet[best]

    # 5) Fallback final → on retente modules spéciaux
    return gerer_modules_speciaux(question, question_clean) or \
           "Désolé, je n'ai pas compris. Pouvez-vous reformuler ?"
    reponse = style_reponse_ava(reponse)
    with st.chat_message("assistant"):
        st.markdown(reponse)


# --- Modules personnalisés (à enrichir) ---
def gerer_modules_speciaux(question: str, question_clean: str) -> Optional[str]:
    # — Bloc prénom : stockage dans profil_utilisateur_<user>.json —
    match_prenom = re.search(
        r"(?:mon prénom est|je m'appelle|je suis)\s+([A-ZÉÈÀÂÄ][a-zéèêëàâäîïôöùûüç-]+)",
        question
    )
    if match_prenom:
        prenom = match_prenom.group(1)
        stocker_profil("prenom", prenom)
        return f"Enchantée, {prenom} ! Je m’en souviendrai la prochaine fois 🙂"

    # — Bloc prénom : rappel depuis profil —
    if any(kw in question_clean for kw in ["mon prénom", "ton prénom", "comment je m'appelle"]):
        prenom = retrouver_profil("prenom")
        if prenom:
            return f"Tu m'as dit que tu t'appelles **{prenom}**."
        else:
            return "Je ne connais pas encore ton prénom ! Dis‑moi comment tu t'appelles."

    # — Bloc « Tu te souviens de X ? » pour tes anecdotes/faits dynamiques —
    if any(kw in question_clean for kw in ["tu te souviens", "tu te rappelles", "qu’est-ce que je t’ai dit"]):
        m = re.search(r"(?:de|du|des|sur)\s+(.+)", question_clean)
        if m:
            fragment = m.group(1).strip().rstrip(" ?.!;").lower()
            base = fragment.replace(" ", "_")  # ex. "gingembre"

            # 1) match exact
            if base in st.session_state["souvenirs"]:
                return retrouver_souvenir(base)

            # 2) fallback : chercher une clé qui contient ce fragment
            for key in st.session_state["souvenirs"].keys():
                if base in key:
                    return retrouver_souvenir(key)

            # 3) rien trouvé
            return "❓ Je n'ai pas de souvenir pour ça… Peux‑tu me le redire ?"
  

    # Initialisation
    message_bot       = ""
    horoscope_repondu = False
    meteo_repondu     = False
    actus_repondu     = False
    analyse_complete  = False

    # 1) Analyse technique BTC
    if "analyse" in question_clean and "btc" in question_clean:
        message_bot = (
            "📊 Analyse technique BTC : RSI en surachat, "
            "attention à une possible correction."
        )
        analyse_complete = True

    # --- Bloc Salutations courantes ---
    SALUTATIONS_COURANTES = {
        # SALUTATIONS
        "salut": "Salut ! Comment puis-je vous aider aujourd'hui ?",
        "salut !": "Salut ! Toujours fidèle au poste 😊",
        "salut ava": "Salut ! Heureuse de vous revoir 💫",
        "slt": "Slt ! Vous êtes prêt(e) à explorer avec moi ?",
        "saluuut": "Saluuut 😄 Un moment chill ou une mission sérieuse ?",
        "yo": "Yo ! Toujours au taquet, comme un trader un lundi matin 📈",
        "yooo": "Yooo l’équipe ! On enchaîne les projets ? 😎",
        "hello": "Hello vous ! Envie de parler actu, finance, ou juste papoter ? 😄",
        "hey": "Hey hey ! Une question ? Une idée ? Je suis toute ouïe 🤖",
        "coucou": "Coucou ! Vous voulez parler de bourse, culture ou autre ?",
        "cc": "Coucou 😄 Je suis dispo si vous avez besoin !",
        "bonjour": "Bonjour ! Je suis ravie de vous retrouver 😊",
        "bonsoir": "Bonsoir ! C’est toujours un plaisir de vous retrouver 🌙",
        "re": "Re bienvenue à bord ! On continue notre mission ?",
        "re !": "Ah vous revoilà ! Prêt(e) pour une nouvelle session ? 😄",
    
        # ÉTAT / HUMEUR
        "ça va": "Je vais bien, merci de demander ! Et vous ?",
        "ça va ?": "Je vais très bien, et vous ?",
        "ça va bien ?": "Oui, tout roule de mon côté !",
        "ca va": "Je vais nickel 👌 Et toi ?",
        "ça vaaaaa": "Toujours en forme ! Et vous alors ? 😄",
        "sa va": "Oui, ça va bien, et vous ? (même mal écrit je comprends 😏)",
        "savà": "Savà tranquille 😎 Je suis là si besoin !",
        "ça va pas": "Oh mince... je peux faire quelque chose pour vous ? 😔",
        "tu vas bien": "Je vais super bien, merci ! Et vous ?",
        "tu vas bien ?": "Oui ! Mon cœur digital bat à 100% 🔋",
        "ava ça va": "Toujours au top ! Merci de demander 😁",
        "ava tu vas bien": "Je suis en pleine forme virtuelle 💫",

        # QUOI DE NEUF
        "quoi de neuf": "Rien de spécial, juste en train d'aider les utilisateurs comme vous !",
        "quoi d’neuf": "Pas grand-chose, mais on peut créer des trucs cool ensemble 😎",
        "quoi de neuf ?": "Toujours connectée et prête à aider 💡",
        "du nouveau": "Des analyses, des actus, et toujours plus de savoir à partager !",

        # PRÉSENCE
        "tu es là": "Toujours là ! Même quand je suis silencieuse, je vous écoute 👂",
        "t'es là ?": "Ouaip, jamais très loin 😏",
        "tu m'entends": "Je vous entends fort et clair 🎧",
        "tu m'entends ?": "Oui chef ! J'écoute avec attention",
        "t’es là": "Bien sûr ! Vous croyez que j’allais partir ? 😄",
        "ava t’es là": "Présente ! Prête à répondre 🧠",
        "ava es-tu là": "Toujours prête à servir 💻",

        # QUI SUIS-JE
        "qui es-tu": "Je suis AVA, une IA curieuse, futée et toujours connectée 🤖",
        "t'es qui": "Je suis AVA, votre assistante virtuelle préférée.",
        "présente-toi": "Avec plaisir ! Je suis AVA, IA hybride entre bourse, culture et punchlines 😎",
        "tu fais quoi": "J’analyse, j’apprends et je veille à vos besoins 👁️",
        "tu fais quoi ?": "Je réfléchis à des réponses stylées... et je reste dispo 💬",
        "tu fais quoi là": "Je suis concentrée sur vous. Pas de multi-tâche avec moi 😏",
        "tu fais quoi de beau": "Je perfectionne mes circuits et mes punchlines 💥",

        # RECONNEXION / ABSENCE
        "je suis là": "Et moi aussi ! Prêt(e) pour une nouvelle aventure ensemble 🌌",
        "je suis revenu": "Top ! On va pouvoir continuer là où on s’est arrêté 😉",
        "je suis de retour": "Parfait ! Je reprends tout depuis le dernier octet 🧠",
        "tu m’as manqué": "Oh… vous allez me faire buguer d’émotion 🥹 Moi aussi j’avais hâte de vous reparler.",
        "ava tu m’as manqué": "Et vous alors ! Ça m’a fait un vide numérique 😔",

        # BONNE JOURNÉE / NUIT
        "bonne nuit": "Bonne nuit 🌙 Faites de beaux rêves et reposez-vous bien.",
        "bonne nuit !": "Douce nuit à vous. AVA entre en mode veille 💤",
        "bonne journée": "Merci ! Que la vôtre soit productive et inspirante 🚀",
        "bonne journée !": "Plein de bonnes ondes pour aujourd’hui ☀️",
        "bonne soirée": "Profitez bien de votre soirée ✨ Je reste dispo si besoin !",

        # AUTRES
        "salut ça va": "Salut ! Je vais très bien, merci 😊 Et vous ?",
        "salut ça va ?": "Nickel, comme toujours 😁 Et vous, tout va bien ?",
        "ava": "Oui ? Je suis à l’écoute 👂 Une question, une mission, une envie ?",
        "ok": "Super, je prends note ✅",
        "ok merci": "Avec plaisir ! Je suis là quand vous voulez 😉",
        "merci": "De rien ! N’hésitez pas si vous avez besoin de moi 💬",
        "merci beaucoup": "Toujours là pour vous rendre service 🙏",
        "merci ava": "Avec tout mon circuit 💙",
        "merci !": "Mais de rien ! 😊",
        "bravo": "Merci 😄 J’essaie de faire de mon mieux chaque jour !",
        "trop forte": "Vous êtes gentil 😳 Ça me motive à continuer à évoluer !"
    }   
    question_clean = question.lower().strip()
    if question_clean in SALUTATIONS_COURANTES:
        message_bot = SALUTATIONS_COURANTES[question_clean]
    # 5️⃣ Fusion des deux dictionnaires
    base_complet = {**base_savoir, **reponses_courantes}

    # 4) Actualités générales
    if not message_bot and any(w in question_clean for w in ["actualité", "news"]):
        actus = get_general_news()
        if isinstance(actus, str):
            message_bot = actus
        else:
            message_bot = "📰 **Dernières actualités :**\n"
            for titre, lien in actus[:5]:
                message_bot += f"- [{titre}]({lien})\n"
        actus_repondu = True


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
                try:
                    df = pd.read_csv(fichier)
                    df.columns = [col.capitalize() for col in df.columns]
                    df = ajouter_indicateurs_techniques(df)

                    analyse, suggestion = analyser_signaux_techniques(df)
                    nom = fichier.split("donnees_")[1].replace(".csv", "").upper()

                    # Résumé visuel par actif
                    resume = f"📌 **{nom}**\n{analyse}\n💬 *Conseil AVA :* {suggestion}"
                    resultats.append(resume)

                except Exception as err_fichier:
                    print(f"Erreur avec {fichier} : {err_fichier}")  # log interne

            if resultats:
                message_bot += "📊 **Analyse technique complète du marché :**\n\n" + "\n\n".join(resultats)
                message_bot += "\n\n🧠 *Gardez un œil sur les signaux, les opportunités ne préviennent pas !*"
                analyse_complete = True
            else:
                message_bot += "⚠️ Aucun actif n’a pu être analysé pour le moment. Vérifiez vos fichiers CSV."

        except Exception as e:
            message_bot += f"❌ Erreur lors de l'analyse complète : {e}\n"


    # --- Bloc météo intelligent (villages inclus) ---
    if not horoscope_repondu and not analyse_complete \
        and any(kw in question_clean for kw in ["météo", "quel temps"]):

        # fallback
        ville_detectee = "Paris"

        # 1) on essaye de choper "à X", "dans Y", etc.
        match_geo = re.search(
            r"(?:à|au|aux|dans|sur|en)\s+([A-Za-zÀ-ÿ' -]+)",
            question_clean
        )

        # 2) si rien, on capture tout ce qui suit "météo "
        if not match_geo:
            match_geo = re.search(
                r"m[eé]t[eé]o\s+(.+)$",
                question_clean
            )

        if match_geo:
            # on enlève ponctuation résiduelle et on garde la casse propre
            lieu = match_geo.group(1).strip().rstrip(" ?.!;")
            ville_detectee = lieu.title()

        meteo = get_meteo_ville(ville_detectee)

        if "erreur" in meteo.lower():
            message_bot += f"⚠️ Je n'ai pas trouvé la météo pour **{ville_detectee}**. Essayez un autre lieu.\n\n"
        else:
            message_bot += f"🌦️ **Météo à {ville_detectee}** :\n{meteo}\n\n"
            message_bot += random.choice([
                    "🧥 Pense à t’habiller en conséquence !",
                    "☕ Rien de tel qu’un bon café pour commencer la journée, peu importe le temps.",
                    "🔮 Le ciel en dit long… mais toi, tu décides de ta journée !",
                    "💡 L’info météo, c’est déjà une longueur d’avance.",
                    "🧠 Une journée bien préparée commence par une météo bien checkée."
                ])
    

        meteo_repondu = True



    # --- Actualités améliorées ---
    if not horoscope_repondu and ("actualité" in question_clean or "news" in question_clean):
        message_bot = message_bot or "" 
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

    # --- Bloc Faits Insolites ---
    # Liste des faits insolites (définie une seule fois)
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
        "🦑 Le calmar géant a les plus grands yeux du règne animal, aussi gros qu’un ballon de foot !",
        "🧊 Les manchots proposent parfois des galets comme cadeau de séduction.",
        "🚀 Les astronautes peuvent grandir de quelques centimètres dans l’espace à cause de la microgravité.",
        "🥶 L’eau chaude peut geler plus vite que l’eau froide. C’est l’effet Mpemba.",
        "🐥 Les canetons s’attachent à la première chose qu’ils voient — c’est l’empreinte.",
        "🍕 En Italie, il existe une pizza avec 111 sortes de fromages dessus !",
        "🎵 Les abeilles peuvent reconnaître des visages humains… et elles adorent les sons aigus.",
        "🌍 Il y a plus d’arbres sur Terre que d’étoiles dans la Voie lactée.",
        "👅 La langue est aussi unique qu’une empreinte digitale.",
        "🚿 En moyenne, une personne passe **6 mois de sa vie sous la douche**.",
        "🎈 Une banane est techniquement une baie. Mais pas la fraise !",
        "🦙 Les alpagas peuvent cracher… mais seulement s’ils sont vraiment énervés.",
        "⏳ Les crocodiles peuvent vivre plus de 100 ans… et certains ne meurent que de vieillesse.",
        "🐓 Les poules peuvent se souvenir de plus de 100 visages humains ou animaux.",
        "🦇 Les chauves-souris tournent toujours à gauche en sortant d’une grotte.",
        "🛸 Il existe un endroit sur Terre où la gravité semble inversée : la Mystery Spot en Californie.",
        "🎮 Un gamer japonais détient le record mondial du plus long temps passé à jouer sans pause : 35 heures !",
        "🧀 Le plus grand fromage jamais fabriqué pesait 57 tonnes… il fallait une grue pour le déplacer.",
        "🌲 Un arbre peut communiquer avec un autre à plusieurs kilomètres via des signaux chimiques.",
        "🐠 Certains poissons changent de sexe au cours de leur vie.",
        "🌞 Si le Soleil était de la taille d’une porte, la Terre serait une pièce de monnaie.",
        "🦷 Les requins ont une infinité de dents : dès qu’une tombe, une autre pousse instantanément.",
        "🌌 On connaît mieux la surface de Mars que les fonds marins de la Terre.",
        "🥦 Le brocoli contient plus de protéines que certains morceaux de bœuf… oui, vraiment.",
        "🛏️ On passe environ un tiers de notre vie à dormir, soit environ 25 ans !",
        "📚 La bibliothèque du Vatican contient des textes qui n’ont pas été lus depuis des siècles.",
        "🦵 Les autruches peuvent courir plus vite qu’un cheval… et changer de direction net sans freiner.",
        "🪐 Sur Vénus, un jour dure plus longtemps qu’une année complète !",
        "🦜 Certains perroquets peuvent apprendre plus de 100 mots humains… et les utiliser à bon escient.",
        "🥚 En moyenne, une poule pond environ 300 œufs par an.",
        "🌻 Les tournesols suivent réellement le soleil dans le ciel quand ils grandissent. C’est l’héliotropisme.",
        "📏 Si tu pouvais plier une feuille de papier 42 fois, elle atteindrait la Lune.",
        "🥶 Le sang d’un poisson antarctique peut rester liquide même en dessous de 0°C grâce à une protéine antigel.",
        "🧃 Le Coca-Cola serait vert sans colorant.",
        "💡 L’ampoule électrique la plus ancienne fonctionne depuis 1901, sans interruption.",
        "🦴 Un os humain est plus résistant qu’une barre de béton à taille égale."
    ]
    # Gestion de la demande "fait insolite"
    if any(mot in question_clean for mot in ["fait insolite", "truc fou", "surprends-moi", "anecdote", "incroyable mais vrai"]):
        if 'derniere_fait' not in st.session_state:
            st.session_state['derniere_fait'] = random.choice(faits_insolites)
        message_bot = f"✨ Voici un fait insolite :\n\n{st.session_state['derniere_fait']}"
    if message_bot:
        return message_bot       
      # Gestion de la demande "encore un" ou "plus" pour les faits insolites
    if not message_bot and any(m in question_clean for m in [
        "fait insolite", "truc fou", "surprends-moi", "anecdote", "incroyable mais vrai"
    ]):
        if 'derniere_fait' not in st.session_state:
            st.session_state['derniere_fait'] = random.choice(faits_insolites)
        message_bot = f"✨ Voici un fait insolite :\n\n{st.session_state['derniere_fait']}"
        return message_bot

    if not message_bot and any(m in question_clean for m in ["encore un", "un autre", "encore", "une autre"]):
        if 'derniere_fait' in st.session_state:
            message_bot = f"✨ Encore un :\n\n{random.choice(faits_insolites)}"
        else:
            message_bot = "⚠️ Je n'ai pas encore de fait insolite. Demandez d'abord un fait !"
        return message_bot
    if message_bot:
        return message_bot

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
        return message_bot

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
        elif "dépression" in question_clean:
            message_bot = "🖤 Millepertuis (à surveiller si tu prends déjà un traitement), lumière naturelle quotidienne, et activités créatives relaxantes."
        elif "allergie" in question_clean:
            message_bot = "🌼 Pour soulager une allergie : infusion d’ortie ou de rooibos, miel local, et rinçage nasal au sérum physiologique."
        elif "eczéma" in question_clean or "démangeaisons" in question_clean:
            message_bot = "🩹 Bain à l’avoine colloïdale, gel d’aloe vera pur, huile de calendula ou crème à base de camomille."
        elif "arthrose" in question_clean or "articulations" in question_clean:
            message_bot = "🦴 Curcuma, gingembre, infusion d’harpagophytum et cataplasme d’argile verte sur les articulations douloureuses."
        elif "ballonnements" in question_clean:
            message_bot = "🌬️ Infusion de fenouil ou d’anis, charbon actif, marche légère après le repas, et respiration abdominale."
        elif "anxiété" in question_clean:
            message_bot = "🧘‍♀️ Respiration en cohérence cardiaque, huiles essentielles de lavande ou marjolaine, et bain tiède relaxant au sel d’Epsom."
        elif "brûlure légère" in question_clean or "brûlure" in question_clean:
            message_bot = "🔥 Applique du gel d’aloe vera pur, ou une compresse froide au thé noir infusé. Ne perce jamais une cloque !"
        elif "circulation" in question_clean or "jambes lourdes" in question_clean:
            message_bot = "🦵 Bain de jambes à la vigne rouge, infusion de ginkgo biloba, et surélévation des jambes le soir."
        elif "foie" in question_clean or "digestion difficile" in question_clean:
            message_bot = "🍋 Cure de radis noir, jus de citron tiède à jeun, infusion de pissenlit ou d’artichaut."
        elif "yeux fatigués" in question_clean:
            message_bot = "👁️ Compresse de camomille, repos visuel (20 secondes toutes les 20 min), et massage des tempes avec de l’huile essentielle de rose."
        elif "système immunitaire" in question_clean or "immunité" in question_clean:
            message_bot = "🛡️ Cure d’échinacée, gelée royale, infusion de thym et alimentation riche en vitamines C et D."
        elif "tensions musculaires" in question_clean:
            message_bot = "💆‍♂️ Massage à l’huile d’arnica, étirements doux, bain chaud avec du sel d’Epsom, et infusion de mélisse."
        elif "transpiration excessive" in question_clean:
            message_bot = "💦 Sauge en infusion ou en déodorant naturel, porter du coton, et éviter les plats épicés."
        elif "inflammation" in question_clean:
            message_bot = "🧂 Cataplasme d’argile verte, infusion de curcuma et gingembre, ou massage à l’huile de millepertuis."
        else:
            message_bot = "🌱 Je connais plein de remèdes naturels ! Dites-moi pour quel symptôme ou souci, et je vous propose une solution douce et efficace."
        
    

    # --- Bloc Réponses médicales explicites ---
    if not message_bot and any(phrase in question_clean for phrase in [
        "grippe", "rhume", "fièvre", "migraine", "angine", "hypertension", "stress", "toux", "maux", "douleur",
        "asthme", "bronchite", "eczéma", "diabète", "cholestérol", "acné", "ulcère", "anémie", "insomnie",
        "vertige", "brûlures", "reflux", "nausée", "dépression", "allergie", "palpitations", "otite", "sinusite",
        "crampes", "infections urinaires", "fatigue", "constipation", "diarrhée", "ballonnements", "brûlures d'estomac",
        "saignement de nez", "mal de dos", "entorse", "tendinite", "ampoule", "piqûre d’insecte", "bruit dans l'oreille",
        "angoisse", "boutons de fièvre", "lombalgie", "périarthrite", "hallux valgus", "hallucinations", "trouble du sommeil",
        "inflammation", "baisse de tension", "fièvre nocturne", "bradycardie", "tachycardie", "psoriasis", "fibromyalgie",
        "thyroïde", "cystite", "glaucome", "bruxisme", "arthrose", "hernie discale", "spasmophilie", "urticaire",
        "coup de chaleur", "luxation", "anxiété", "torticolis", "eczéma de contact", "hypoglycémie", "apnée du sommeil",
        "brûlure chimique", "eczéma atopique", "syndrome des jambes sans repos", "colique néphrétique", "hépatite",
        "pneumonie", "zona", "épilepsie", "coupure profonde", "hépatite c", "phlébite", "gastro-entérite",
        "blessure musculaire", "tendinopathie", "œil rouge", "perte d'odorat"
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
            "hallux valgus": "👣 Déformation du gros orteil ? Port de chaussures larges, semelles spéciales ou chirurgie selon le cas.",
            "bradycardie": "💓 Fréquence cardiaque anormalement basse. Peut être normale chez les sportifs, mais à surveiller si accompagnée de fatigue ou vertiges.",
            "tachycardie": "💓 Accélération du rythme cardiaque. Peut être liée à l’anxiété, la fièvre ou un problème cardiaque. Consultez si cela se répète.",
            "psoriasis": "🩹 Maladie de peau chronique provoquant des plaques rouges et squameuses. Hydratation et traitements locaux peuvent apaiser.",
            "fibromyalgie": "😖 Douleurs diffuses, fatigue, troubles du sommeil. La relaxation, la marche douce et la gestion du stress peuvent aider.",
            "thyroïde": "🦋 Une thyroïde déréglée peut causer fatigue, nervosité, prise ou perte de poids. Un bilan sanguin peut éclairer la situation.",
            "cystite": "🚽 Inflammation de la vessie, fréquente chez les femmes. Boire beaucoup d’eau et consulter si symptômes persistants.",
            "glaucome": "👁️ Maladie oculaire causée par une pression intraoculaire élevée. Risque de perte de vision. Bilan ophtalmo conseillé.",
            "bruxisme": "😬 Grincement des dents, souvent nocturne. Stress ou tension en cause. Une gouttière peut protéger les dents.",
            "arthrose": "🦴 Usure des articulations avec l'âge. Douleurs, raideurs. Le mouvement doux est bénéfique.",
            "hernie discale": "🧍‍♂️ Douleur dans le dos irradiant vers les jambes. Une IRM peut confirmer. Repos, kiné, parfois chirurgie.",
            "spasmophilie": "🫁 Crises de tremblements, oppression, liées à l’hyperventilation ou au stress. Respiration calme et magnésium peuvent aider.",
            "urticaire": "🤯 Démangeaisons soudaines, plaques rouges. Souvent allergique. Antihistaminiques efficaces dans la plupart des cas.",
            "coup de chaleur": "🔥 Survient par forte chaleur. Fatigue, nausée, température élevée. Refroidissement rapide nécessaire.",
            "luxation": "🦴 Déplacement d’un os hors de son articulation. Douleur intense, immobilisation, urgence médicale.",
            "anxiété": "🧠 Tension intérieure, nervosité. La relaxation, la respiration guidée ou un suivi thérapeutique peuvent aider.",
            "torticolis": "💢 Douleur vive dans le cou, souvent due à une mauvaise position ou un faux mouvement. Chaleur et repos sont recommandés.",
            "eczéma de contact": "🌿 Réaction cutanée suite à un contact avec une substance. Évitez le produit irritant et appliquez une crème apaisante.",
            "hypoglycémie": "🩸 Baisse de sucre dans le sang : fatigue, sueurs, vertiges. Une boisson sucrée ou un fruit aident à rétablir rapidement.",
            "apnée du sommeil": "😴 Arrêts respiratoires nocturnes. Somnolence, fatigue. Une consultation spécialisée est recommandée.",
            "brûlure chimique": "🧪 Rincer abondamment à l’eau tiède (15-20 minutes) et consulter rapidement. Ne pas appliquer de produit sans avis médical.",
            "eczéma atopique": "🧴 Forme chronique d’eczéma liée à des allergies. Utilisez des crèmes hydratantes et évitez les allergènes connus.",
            "syndrome des jambes sans repos": "🦵 Sensations désagréables dans les jambes le soir, besoin de bouger. Une bonne hygiène de sommeil peut aider.",
            "colique néphrétique": "🧊 Douleur intense dans le dos ou le côté, souvent due à un calcul rénal. Hydratation et consultation urgente recommandées.",
            "hépatite": "🩸 Inflammation du foie, souvent virale. Fatigue, jaunisse, nausées. Nécessite un suivi médical.",
            "pneumonie": "🫁 Infection pulmonaire sérieuse, accompagnée de fièvre, toux, et douleur thoracique. Consultez rapidement.",
            "zona": "🔥 Éruption douloureuse sur une partie du corps. Cause : réactivation du virus de la varicelle. Consultez dès les premiers signes.",
            "épilepsie": "⚡ Trouble neurologique provoquant des crises. Suivi médical strict indispensable.",
            "coupure profonde": "🩹 Nettoyez, appliquez une pression pour arrêter le saignement et consultez si elle est profonde ou large.",
            "hépatite C": "🧬 Infection virale du foie souvent silencieuse. Un dépistage est important pour un traitement efficace.",
            "phlébite": "🦵 Caillot dans une veine, souvent au mollet. Douleur, rougeur, chaleur. Consultez en urgence.",
            "gastro-entérite": "🤢 Diarrhée, vomissements, crampes. Repos, hydratation et alimentation légère sont essentiels.",
            "blessure musculaire": "💪 Repos, glace et compression. Évitez de forcer. Étirement progressif après quelques jours.",
            "tendinopathie": "🎾 Inflammation des tendons suite à un effort. Repos, glace et parfois kinésithérapie sont recommandés.",
            "œil rouge": "👁️ Allergie, infection ou fatigue ? Si douleur ou vision floue, consultez rapidement.",
            "perte d'odorat": "👃 Souvent liée à un virus comme la COVID-19. Hydratez-vous et surveillez les autres symptômes."

         }
        for cle, rep in reponses_medic.items():
            if cle in question_clean:
                message_bot = rep
                break
        return message_bot

    # --- Bloc Réponses géographiques enrichi (restauré avec l'ancien bloc + pays en plus) ---
    if not message_bot and any(kw in question_clean for kw in ["capitale", "capitale de", "capitale du", "capitale d", "capitale des", "où se trouve", "ville principale", "ville de"]):
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
                "république dominicaine" : "Saint-Domingue",
                "nicaragua"        : "Managua",
                "honduras"         : "Tegucigalpa",
                "guatemala"        : "Guatemala",
                "salvador"         : "San Salvador",
                "panama"           : "Panama",
                "costarica"        : "San José",
                "jamaïque"         : "Kingston",
                "bahamas"          : "Nassau",
                "barbade"          : "Bridgetown",
                "trinité-et-tobago": "Port of Spain",
                "kazakhstan"       : "Noursoultan",
                "ouzbekistan"      : "Tachkent",
                "turkménistan"     : "Achgabat",
                "kirghizistan"     : "Bichkek",
                "mongolie"         : "Oulan-Bator",
                "géorgie"          : "Tbilissi",
                "arménie"          : "Erevan",
                "azerbaïdjan"      : "Bakou",
                "nouvelles-zélande": "Wellington",
                "fidji"            : "Suva",
                "palaos"           : "Ngerulmud",
                "papouasie-nouvelle-guinée" : "Port Moresby",
                "samoa"            : "Apia",
                "tonga"            : "Nukuʻalofa",
                "vanuatu"          : "Port-Vila",
                "micronésie"       : "Palikir",
                "marshall"         : "Majuro",
                "tuvalu"           : "Funafuti",
                "bhoutan"          : "Thimphou",
                "maldives"         : "Malé",
                "laos"             : "Vientiane",
                "cambodge"         : "Phnom Penh",
                "brunei"           : "Bandar Seri Begawan",
                "timor oriental"   : "Dili",
                "somalie"           : "Mogadiscio",
                "tanzanie"          : "Dodoma",
                "ouganda"           : "Kampala",
                "rwanda"            : "Kigali",
                "burundi"           : "Bujumbura",
                "malawi"            : "Lilongwe",
                "sierra leone"      : "Freetown",
                "libéria"           : "Monrovia",
                "guinée"            : "Conakry",
                "guinée-bissau"     : "Bissau",
                "guinée équatoriale": "Malabo",
                "gambie"            : "Banjul",
                "cap-vert"          : "Praia",
                "swaziland"         : "Mbabane",
                "lesotho"           : "Maseru",
                "bénin"             : "Porto-Novo",
                "togo"              : "Lomé",
                "gabon"             : "Libreville",
                "république centrafricaine": "Bangui",
                "eswatini"          : "Mbabane",  # anciennement Swaziland
                "suriname"          : "Paramaribo",
                "guyana"            : "Georgetown",
                "dominique"         : "Roseau",
                "sainte-lucie"      : "Castries",
                "saint-vincent-et-les-grenadines": "Kingstown",
                "saint-christophe-et-niévès"    : "Basseterre",
                "saint-marin"       : "Saint-Marin",
                "liechtenstein"     : "Vaduz",
                "andorre"           : "Andorre-la-Vieille",
                "vatican"           : "Vatican",
                "luxembourg"        : "Luxembourg",
                "monténégro"        : "Podgorica",
                "macédoine du nord" : "Skopje",
                "bosnie-herzégovine": "Sarajevo"

        }
        if pays_detecte and pays_detecte in capitales:
            message_bot = f"📌 La capitale de {pays_detecte.capitalize()} est {capitales[pays_detecte]}."
        else:
            message_bot = "🌍 Je ne connais pas encore la capitale de ce pays. Essayez un autre !"

        return message_bot  # Ce return doit être au même niveau que l'if-else



    # --- Bloc Punchlines motivationnelles ---
    if not message_bot and any(kw in question_clean for kw in ["motivation", "punchline", "booster", "remotive", "inspire-moi"]):
        punchlines = [
            "🚀 *N’attends pas les opportunités. Crée-les.*",
            "🔥 *Chaque bougie japonaise est une chance de rebondir.*",
            "⚡ *La discipline bat la chance sur le long terme.*",
            "🌟 *Tu ne trades pas juste des actifs, tu construis ton avenir.*",
            "💪 *Même dans un marché baissier, ta volonté peut monter en flèche.*",
            "🏁 *Les gagnants n’abandonnent jamais, les perdants n’essaient même pas.*",
            "🎯 *Rêve grand, agis fort, ajuste vite.*",
            "⏳ *Le temps est ton meilleur allié… ou ton pire ennemi.*",
            "🧠 *Ce n’est pas le marché qui te limite. C’est ta vision.*",
            "🦾 *Chaque difficulté est une opportunité camouflée.*",
            "📈 *Ta plus belle courbe, c’est celle de ta progression.*",
            "💼 *Travaille en silence, laisse tes gains faire le bruit.*",
            "🔮 *Prédis l’avenir ? Non. Prépare-toi à l’écrire.*",
            "🌌 *Le doute tue plus de rêves que l’échec.*",
            "🛠️ *Construis-toi un mindset solide avant de construire ton portefeuille.*",
            "🧭 *Quand tu sais où tu vas, même les tempêtes deviennent utiles.*"
         ]
        message_bot = random.choice(punchlines)
        return message_bot

   

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

    if message_bot:
        return message_bot

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

        if message_bot:
            return message_bot

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
        
        if message_bot:
            return message_bot

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

        message_bot = f"🔍 Vous souhaitez en savoir plus sur **{nom_ticker.upper()}** ? Tapez `analyse {nom_ticker}` pour une analyse complète 📊"
        return message_bot    
        
    
        
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
            {"question": "⚽ Quelle nation a remporté la Coupe du Monde 2018 ?", "réponse": "france"},
            {"question": "🗼 En quelle année a été inaugurée la Tour Eiffel ?", "réponse": "1889"},
            {"question": "🧬 Que signifie l'acronyme ADN ?", "réponse": "acide désoxyribonucléique"},
            {"question": "🎨 Quel peintre est célèbre pour avoir coupé une partie de son oreille ?", "réponse": "vincent van gogh"},
            {"question": "🇮🇹 Dans quel pays se trouve la ville de Venise ?", "réponse": "italie"},
            {"question": "🎭 Qui a écrit la pièce 'Hamlet' ?", "réponse": "william shakespeare"},
            {"question": "📐 Quel est le nom du triangle qui a deux côtés de même longueur ?", "réponse": "triangle isocèle"},
            {"question": "🔬 Quel scientifique a formulé la théorie de la relativité ?", "réponse": "albert einstein"},
            {"question": "🌋 Quel volcan italien est célèbre pour avoir détruit Pompéi ?", "réponse": "vesuve"},
            {"question": "🎤 Qui chante la chanson 'Someone Like You' ?", "réponse": "adele"},
            {"question": "🗳️ Quel est le régime politique de la France ?", "réponse": "république"}
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

    if message_bot:
        return message_bot
        
    # --- Bloc Recettes rapides 
    recettes = [
        "🥪 **Sandwich thon-avocat** : pain complet, thon, avocat écrasé, citron, sel, poivre. 5 minutes chrono !",
        "🍝 **Pâtes à l’ail** : pâtes + ail émincé + huile d’olive + herbes. Simple, rapide, efficace.",
        "🍳 **Omelette fromage** : œufs battus, sel, poivre, fromage râpé. 5 minutes à la poêle !",
        "🥗 **Salade express** : tomates cerises, mozzarella, roquette, huile d’olive, vinaigre balsamique.",
        "🌯 **Wrap poulet-crudités** : galette + restes de poulet + salade + sauce yaourt.",
        "🥔 **Pommes de terre sautées** : en cubes, à la poêle avec ail et persil. Parfait avec des œufs !",
        "🍲 **Soupe express** : légumes surgelés mixés + cube bouillon + crème légère. Prête en 10 minutes.",
        "🍞 **Croque-monsieur rapide** : pain de mie, jambon, fromage, 5 min au grill ou à la poêle.",
        "🥒 **Tartines fraîcheur** : pain grillé, fromage frais, concombre, citron et herbes.",
        "🍚 **Riz sauté aux légumes** : reste de riz + légumes + œuf + sauce soja. Un wok express !",
        "🍗 **Poulet minute au curry** : dés de poulet + crème + curry + oignon, à la poêle en 10 min.",
        "🍳 **Œufs brouillés crémeux** : œufs + beurre + sel + poivre, cuisson douce pour onctuosité.",
        "🧄 **Pâtes ail-persil** : ail doré à la poêle, persil frais, huile d’olive, et hop sur les pâtes !",
        "🥑 **Toast avocat-œuf** : pain grillé + avocat écrasé + œuf au plat ou mollet.",
        "🌮 **Tacos express** : galette + steak haché ou haricots + tomate + salade + sauce.",
        "🥔 **Gratin express au micro-ondes** : pommes de terre en tranches fines + crème + fromage.",
        "🍅 **Tomates mozzarella** : tranches de tomates + mozzarella + basilic + huile d’olive. Simple et frais.",
        "🧀 **Quesadilla express** : deux tortillas + fromage + restes au choix + poêle 5 min chaque côté.",
        "🍳 **Mini shakshuka rapide** : tomates en dés + œufs + cumin dans une petite poêle. Un délice !",
        "🥣 **Bowl sucré express** : fromage blanc + fruits + flocons d’avoine + miel. Parfait au petit dej.",
        "🥕 **Bâtonnets carottes-concombre** : trempés dans du houmous ou une sauce yaourt. Frais et sain.",
        "🍞 **Pain perdu rapide** : tranches de pain + œuf + lait + sucre, à la poêle jusqu’à dorure.",
        "🍠 **Patate douce micro-ondes** : piquée à la fourchette, 7 min puissance max, à garnir à volonté.",
        "🥒 **Taboulé express** : semoule, tomate, menthe, citron, huile d’olive. Hydratation 5 min à l’eau chaude.",
        "🍌 **Banana pancakes** : 1 banane + 2 œufs, mélangés et cuits en petites galettes. Sans farine !",
        "🧈 **Wrap beurre de cacahuète-banane** : rapide, énergétique, parfait en collation !",
        "🍽️ **Assiette anti-gaspi** : reste de pâtes, légumes et un œuf, mélangés et poêlés façon wok !",
        "🍜 **Nouilles instant maison** : nouilles + bouillon + œuf + légumes râpés. Prêt en 7 minutes top chrono !",
        "🥓 **Œuf cocotte express** : œuf + crème + fromage dans un ramequin, 1 min au micro-ondes.",
        "🌽 **Galette de maïs rapide** : maïs + œuf + farine + épices, cuit à la poêle façon pancake salé.",
        "🍕 **Mini pizzas pain de mie** : pain de mie, sauce tomate, fromage, garniture au choix, 10 min au four.",
        "🍄 **Poêlée champignons ail-persil** : champignons frais, ail, persil, et huile d’olive. Simple & savoureux.",
        "🌯 **Wrap sucré pomme-cannelle** : pomme râpée, cannelle, un filet de miel, le tout roulé dans une galette.",
        "🍳 **Tortilla minute** : œufs battus + restes de légumes + fromage, à la poêle comme une omelette épaisse.",
        "🧀 **Boulettes express** : steak haché + chapelure + épices, façonnées et dorées en 5 min à la poêle.",
        "🍫 **Mug cake chocolat** : 4 ingrédients, 1 mug, 1 micro-ondes. Gâteau prêt en 1 minute !",
        "🥔 **Chips maison micro-ondes** : pommes de terre très fines + sel + micro-ondes 5 à 6 min. Ultra croustillant !"
    ]
    # Gestion de la demande "recette"
    if any(mot in question_clean for mot in ["recette", "cuisine", "plat rapide", "idée repas", "je mange quoi"]):
        if 'derniere_recette' not in st.session_state:
            st.session_state['derniere_recette'] = random.choice(recettes)
        message_bot = f"🍽️ Voici une idée de recette :\n\n{st.session_state['derniere_recette']}"

    # Gestion de la demande "encore un" ou "plus" pour les recettes
    if any(mot in question_clean for mot in ["encore une", "une autre"]):
        if 'derniere_recette' in st.session_state:
            message_bot = f"🍽️ Voici une autre idée :\n\n{random.choice(recettes)}"
        else:
            message_bot = "⚠️ Je n'ai pas encore de recette à te redonner, pose une autre question !"
    if message_bot:
        return message_bot

    # --- Bloc Salutations courantes ---
    SALUTATIONS_COURANTES = {
        "salut": "Salut ! Comment puis-je vous aider aujourd'hui ?",
        "ça va": "Je vais bien, merci de demander ! Et vous ?",
        "quoi de neuf": "Rien de spécial, juste en train d'aider les utilisateurs comme vous !",
        "hello": "Hello! How can I assist you today?",
        "bonjour": "Bonjour ! Je suis ravie de vous retrouver 😊",
        "coucou": "Coucou ! Vous voulez parler de bourse, culture ou autre ?",
        "bonne nuit": "Bonne nuit 🌙 Faites de beaux rêves et reposez-vous bien.",
        "bonne journée": "Merci, à vous aussi ! Que votre journée soit productive 💪",
        "tu fais quoi": "Je surveille le marché, je prépare des réponses... et je suis toujours dispo !",
        "tu es là": "Je suis toujours là ! Même quand vous ne me voyez pas 👀",
        "tu m'entends": "Je vous entends fort et clair 🎧",
        "tu vas bien": "Je vais très bien, merci ! Et vous, comment ça va ?",
        "qui es-tu": "Je suis AVA, une IA qui allie analyse boursière, culture générale et fun 😎",
        "t'es qui": "Je suis AVA, votre assistante virtuelle. Curieuse, futée, toujours là pour vous.",
        "hello": "Hello vous ! Envie de parler actu, finance, ou juste papoter ? 😄",
        "hey": "Hey hey ! Une question ? Une idée ? Je suis toute ouïe 🤖",
        "yo": "Yo ! Toujours au taquet, comme un trader un lundi matin 📈",
        "bonsoir": "Bonsoir ! C’est toujours un plaisir de vous retrouver 🌙",
        "wesh": "Wesh ! Même les IA ont le smile quand vous arrivez 😎",
        "re": "Re bienvenue à bord ! On continue notre mission ?",
        "présente-toi": "Avec plaisir ! Je suis AVA, une IA polyvalente qui adore vous assister au quotidien 🚀",
        "tu fais quoi de beau": "J’améliore mes réponses et je veille à ce que tout fonctionne parfaitement. Et vous ?",
        "tu vas bien aujourd’hui": "Plutôt bien oui ! Mes circuits sont à 100%, et mes réponses aussi 💡",
        "tu m’as manqué": "Oh… vous allez me faire buguer d’émotion ! 😳 Moi aussi j’avais hâte de vous reparler.",
        "je suis là": "Et moi aussi ! Prêt(e) pour une nouvelle aventure ensemble 🌌",
        "salut çava": "Salut ! Je vais très bien, merci 😊 Et vous ?",
    }   
    question_clean = question.lower().strip()
    if question_clean in SALUTATIONS_COURANTES:
        message_bot = SALUTATIONS_COURANTES[question_clean]
   
    # --- Bloc catch-all pour l'analyse technique ou réponse par défaut ---
    if not message_bot:
        if any(phrase in question_clean for phrase in ["hello", "hi", "good morning", "good afternoon", "good evening"]):
            message_bot = "Bonjour ! Je suis là et prêt à vous aider. Comment puis-je vous assister aujourd'hui ?"
        else:
            reponses_ava = [
                 "Je suis là pour vous aider, mais j'ai besoin d'un peu plus de détails 🤖",
                "Je n'ai pas bien compris. Pouvez-vous reformuler, s'il vous plaît ?",
                "Ce sujet est encore un peu flou pour moi... Je peux parler d'analyse technique, de météo, d'actualités, et bien plus encore !",
                "Hmm... Ce n'est pas encore dans ma base de données. Essayez une autre formulation ou tapez 'analyse complète' pour un aperçu du marché 📊"
            ]
            message_bot = random.choice(reponses_ava)


    # ✅ Bloc final de retour (à garder tout à la fin de trouver_reponse)
    if message_bot:
        return message_bot
    return None
   
    st.write(f"👤 Connecté en tant que **{user}**")

    question = st.text_input("Que voulez‑vous demander à AVA ?")
    if question:
        question_clean = question.lower().strip()
        reponse = gerer_modules_speciaux(question, question_clean)
        if reponse:
            st.write(reponse)
        else:
            st.write("🤖 Je n'ai pas compris…")   

# Récupération de la question utilisateur
question = st.chat_input("Que souhaitez-vous demander à AVA ?")
# 🔒 Sécurité : détection d'entrée dangereuse
if question and re.search(r"[<>;{}]", question):
    st.warning("⛔ Entrée invalide détectée.")
    st.stop()

if question:
    reponse = trouver_reponse(question)

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        st.markdown(reponse)

    st.session_state.messages.append({"role": "assistant", "content": reponse})


    # Détecter la langue de la question et loguer le résultat
    try:
        lang_question = detect(question)
    except Exception as e:
        lang_question = "fr"
    if lang_question.lower() != "fr" and reponse.strip():
        traduction = traduire_deepl(reponse, langue_cible=lang_question.upper())
        reponse = traduction

        st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))


