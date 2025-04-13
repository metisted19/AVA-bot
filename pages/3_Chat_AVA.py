import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville
import requests
from PIL import Image

# Configuration de la page Streamlit
st.set_page_config(page_title="Chat AVA", layout="centered")

# Affichage du message d'accueil avec logo personnalisé
st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <img src='https://ava-bot-a8bcqxjmaej5yqe8tcrdgq.streamlit.app/assets/ava_logo.png' width='40' style='margin-bottom: -8px;'>
        <h1 style='margin: 0; font-size: 2rem;'>AVA - Chat IA</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités... ou juste pour discuter !")

# Initialisation de l'historique de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Affichage des messages existants ---
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="assets/ava_logo.png"):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Interaction principale ---
question = st.chat_input("Que souhaitez-vous demander à AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="assets/ava_logo.png"):
        question_clean = question.lower().strip()
        message_bot = ""

        # --- Horoscope ---
        if "horoscope" in question_clean or "signe" in question_clean or "astrologie" in question_clean:
            signes = ["bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance", "scorpion", "sagittaire", "capricorne", "verseau", "poissons"]
            signes_api = {
                "bélier": "aries", "taureau": "taurus", "gémeaux": "gemini",
                "cancer": "cancer", "lion": "leo", "vierge": "virgo",
                "balance": "libra", "scorpion": "scorpio", "sagittaire": "sagittarius",
                "capricorne": "capricorn", "verseau": "aquarius", "poissons": "pisces"
            }
            signe_detecte = next((s for s in signes if s in question_clean), None)

            if not signe_detecte:
                message_bot = "🔮 Pour vous donner votre horoscope, indiquez-moi votre **signe astrologique** (ex : Lion, Vierge...)."
            else:
                try:
                    signe_api = signes_api.get(signe_detecte, "")
                    url = f"https://aztro.sameerkumar.website/?sign={signe_api}&day=today"
                    response = requests.post(url)
                    if response.status_code == 200:
                        data = response.json()
                        message_bot = f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {data['description']}"
                    else:
                        message_bot = "❌ Désolé, impossible d'obtenir l'horoscope pour le moment."
                except Exception as e:
                    message_bot = f"⚠️ Une erreur est survenue : {e}"

        # --- Commande secrète : analyse complète ou synonymes ---
        elif any(phrase in question_clean for phrase in ["analyse complète", "analyse des marchés", "analyse technique", "prévision boursière"]):
            import glob
            try:
                resultats = []
                fichiers = glob.glob("data/donnees_*.csv")
                for fichier in fichiers:
                    df = pd.read_csv(fichier)
                    df.columns = [col.capitalize() for col in df.columns]
                    try:
                        analyse, suggestion = analyser_signaux_techniques(df)
                        nom = fichier.split("donnees_")[1].replace(".csv", "").upper()
                        resume = f"\n📌 **{nom}**\n{analyse}\n📁 {suggestion}"
                        resultats.append(resume)
                    except:
                        continue
                message_bot = "📊 **Analyse complète du marché :**\n" + "\n\n".join(resultats[:5])
            except Exception as e:
                message_bot = f"❌ Erreur lors de l'analyse complète : {e}"

        # --- Actualités avec résumé ---
        elif "actualité" in question_clean or "news" in question_clean:
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot = actus
            elif actus:
                resume = "".join([titre for titre, _ in actus[:3]])
                message_bot = "🧔️ Les actus bougent ! Voici un résumé :\n\n"
                message_bot += f"*En bref* : {resume[:180]}...\n\n"
                message_bot += "🔖 Articles à lire :\n" + "\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus])
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

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

# Bouton pour effacer les messages uniquement
st.sidebar.button("🪛 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))































