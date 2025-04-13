import streamlit as st
import os
import pandas as pd
import requests
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville

st.set_page_config(page_title="Chat AVA", layout="centered")

st.title("🤖 AVA - Chat IA")
st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités, votre horoscope... ou juste pour discuter !")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Fonction horoscope ---
def get_horoscope(sign):
    url = "https://kayoo123.github.io/astroo-api/jour.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            horoscope = data.get(sign.lower())
            if horoscope:
                return f"🔮 Horoscope du jour pour {sign.capitalize()} :\n{horoscope}"
            else:
                return "Désolé, je n'ai pas trouvé ton signe astrologique."
        else:
            return "Désolé, je n'ai pas pu récupérer l'horoscope pour aujourd'hui."
    except Exception as e:
        return f"Une erreur est survenue : {e}"

# --- Affichage historique ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input utilisateur ---
question = st.chat_input("Que souhaitez-vous demander à AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        question_clean = question.lower().strip()
        message_bot = ""

        if "horoscope" in question_clean or "signe" in question_clean:
            st.markdown("Quel est votre signe astrologique ?")
            sign = st.text_input("Saisissez votre signe :", key="signe_astrologique")
            if sign:
                message_bot = get_horoscope(sign)

        elif "actualité" in question_clean or "news" in question_clean:
            actus = get_general_news()
            if isinstance(actus, str):
                message_bot = actus
            elif actus:
                message_bot = "📰 Voici les actualités :\n\n" + "\n\n".join([f"🔹 [{titre}]({lien})" for titre, lien in actus])
            else:
                message_bot = "❌ Aucune actualité disponible pour le moment."

        elif "météo" in question_clean or "quel temps" in question_clean:
            ville_detectee = "Paris"
            for mot in question.split():
                if mot and mot[0].isupper() and len(mot) > 2:
                    ville_detectee = mot
            message_bot = get_meteo_ville(ville_detectee)

        elif any(phrase in question_clean for phrase in ["ça va", "comment tu vas", "tu vas bien"]):
            message_bot = "Je vais super bien, prête à analyser le monde avec vous ! Et vous ?"

        elif any(phrase in question_clean for phrase in ["quoi de neuf", "tu fais quoi", "des news"]):
            message_bot = "Je scrute les marchés, je capte les tendances… une journée normale pour une IA boursière !"

        elif any(phrase in question_clean for phrase in ["t'es qui", "tu es qui", "t'es quoi", "tu es quoi"]):
            message_bot = "Je suis AVA, votre assistante virtuelle boursière, météo, horoscope et plus encore. Une alliée du futur."

        elif any(phrase in question_clean for phrase in ["tu dors", "t'es là", "tu es là"]):
            message_bot = "Je ne dors jamais. Toujours connectée, toujours prête. Posez votre question !"

        elif "salut" in question_clean or "bonjour" in question_clean:
            message_bot = "👋 Bonjour mon ami ! Besoin d'une analyse, d'un conseil ou d'un petit moment fun ? 😊"

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

            if not os.path.exists(data_path):
                try:
                    import yfinance as yf
                    df = yf.download(nom_ticker, period="6mo", interval="1d")
                    df.to_csv(data_path, index=True)
                except Exception as e:
                    message_bot = f"❌ Impossible de télécharger les données pour {nom_ticker.upper()} : {e}"

            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                df.columns = [col.capitalize() for col in df.columns]

                if "Close" not in df.columns:
                    st.warning(f"⚠️ Les données pour {nom_ticker.upper()} sont invalides. Aucune colonne 'Close' trouvée. (Colonnes : {', '.join(df.columns)})")
                else:
                    try:
                        analyse, suggestion = analyser_signaux_techniques(df)
                        message_bot = (
                            f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n"
                            f"{analyse}\n\n"
                            f"🤖 *Mon intuition d'AVA ?* {suggestion}"
                        )
                    except Exception as e:
                        message_bot = f"⚠️ Une erreur est survenue pendant l'analyse : {e}"
            else:
                message_bot = f"⚠️ Je n’ai pas pu récupérer les données pour {nom_ticker.upper()}"

        else:
            message_bot = obtenir_reponse_ava(question)

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

st.sidebar.button("🧹 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))















