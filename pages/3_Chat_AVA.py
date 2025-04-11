import streamlit as st
import os
import pandas as pd
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat import obtenir_reponse_ava
from fonctions_actualites import obtenir_actualites, get_general_news
from fonctions_meteo import obtenir_meteo, get_meteo_ville

st.set_page_config(page_title="Chat AVA", layout="centered")

st.title("🤖 AVA - Chat IA")
st.markdown("Posez-moi vos questions sur la bourse, la météo, les actualités... ou juste pour discuter !")

# Historique de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Fonction d'analyse de sentiment --- 
def analyser_sentiment(news_list):
    mots_positifs = ["progress", "gain", "rise", "success", "growth"]
    mots_negatifs = ["fall", "loss", "drop", "crash", "recession"]
    score = 0
    for titre, _ in news_list:
        titre = titre.lower()
        score += sum(1 for mot in mots_positifs if mot in titre)
        score -= sum(1 for mot in mots_negatifs if mot in titre)
    if score > 1:
        return "🟢 Le sentiment global du marché est **positif**."
    elif score < -1:
        return "🔴 Le sentiment global du marché est **négatif**."
    else:
        return "🟡 Le sentiment global du marché est **neutre**."

# --- Affichage des messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Interaction ---
question = st.chat_input("Que souhaitez-vous demander à AVA ?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        question_clean = question.lower().strip()
        message_bot = ""

        if "actualité" in question_clean or "news" in question_clean:
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
            message_bot = "Je suis AVA, votre assistante virtuelle boursière, météo, et bien plus. Disons... une alliée du futur."

        elif any(phrase in question_clean for phrase in ["tu dors", "t'es là", "tu es là"]):
            message_bot = "Je ne dors jamais. Toujours connectée, toujours prête. Posez votre question !"

        elif "salut" in question_clean or "bonjour" in question_clean:
            message_bot = "👋 Bonjour ! Je suis AVA. Besoin d'une analyse ou d'un coup de pouce ? 😊"

        elif any(symb in question_clean for symb in ["aapl", "tsla", "googl", "btc", "eth", "fchi", "cac"]):
            mapping = {
                "btc": "btc-usd",
                "eth": "eth-usd",
                "aapl": "aapl",
                "tsla": "tsla",
                "googl": "googl",
                "fchi": "^fchi",
                "cac": "^fchi"
            }

            for symb, ticker in mapping.items():
                if symb in question_clean:
                    nom_ticker = ticker
                    break
            else:
                nom_ticker = question_clean

            data_path = f"data/donnees_{nom_ticker}.csv"

            if not os.path.exists(data_path):
                message_bot = f"⚠️ Je n’ai pas trouvé les données pour {nom_ticker.upper()}.\nLancez le script d'entraînement pour les générer."
            else:
                df = pd.read_csv(data_path)
                df.columns = [col.capitalize() for col in df.columns]  # standardise les noms

                if "Close" not in df.columns:
                    colonnes_dispo = ', '.join(df.columns.tolist())
                    message_bot = (
                        f"⚠️ Les données pour {nom_ticker.upper()} sont invalides. "
                        f"Aucune colonne 'Close' trouvée.\n"
                        f"(Colonnes présentes : {colonnes_dispo})"
                    )
                else:
                    df = ajouter_indicateurs_techniques(df)
                    try:
                        analyse, suggestion = analyser_signaux_techniques(df)
                        message_bot = (
                            f"📊 Voici mon analyse technique pour **{nom_ticker.upper()}** :\n\n"
                            f"{analyse}\n\n"
                            f"🤖 *Mon intuition d'IA ?* {suggestion}"
                        )
                        # Résumé rapide intelligent
                        resume_parts = []

                        if 'rsi' in df.columns:
                        rsi = df['rsi'].iloc[-1]
                        if rsi < 30:
                           resume_parts.append(f"RSI à {rsi:.0f} (survendu)")
                        elif rsi > 70:
                            resume_parts.append(f"RSI à {rsi:.0f} (suracheté)")

                        if 'macd' in df.columns and 'macd_signal' in df.columns:
                            macd = df['macd'].iloc[-1]
                            signal = df['macd_signal'].iloc[-1]
                            if macd > signal:
                               resume_parts.append("MACD en croisement haussier")
                            elif macd < signal:
                                resume_parts.append("MACD en croisement baissier")

                        if resume_parts:
                            message_bot += "\n\n✅ **Résumé rapide :** " + ", ".join(resume_parts) + "."

                    except Exception as e:
                        message_bot = f"⚠️ Une erreur est survenue pendant l'analyse : {e}"

        else:
            message_bot = obtenir_reponse_ava(question)

        st.markdown(message_bot)
        st.session_state.messages.append({"role": "assistant", "content": message_bot})

# Bouton pour effacer les messages uniquement
st.sidebar.button("🧹 Effacer les messages", on_click=lambda: st.session_state.__setitem__("messages", []))
