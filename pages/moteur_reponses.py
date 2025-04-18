import re
import random
import requests
import os
import pandas as pd
from outils_ava import (
    ajouter_indicateurs_techniques,
    analyser_signaux_techniques,
    get_meteo_ville,
    get_general_news,
    remove_accents
)

def traiter_question(question_raw: str) -> str:
    question_clean = question_raw.lower().strip()
    message_bot = ""

    # --- Horoscope ---
    if any(mot in question_clean for mot in ["horoscope", "signe", "astrologie"]):
        signes_disponibles = [
            "bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance",
            "scorpion", "sagittaire", "capricorne", "verseau", "poissons"
        ]
        signe_detecte = next((s for s in signes_disponibles if s in question_clean), None)
        if not signe_detecte:
            return "🔮 Pour vous donner votre horoscope, indiquez-moi votre **signe astrologique** (ex : Lion, Vierge...)."
        try:
            url = "https://kayoo123.github.io/astroo-api/jour.json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                horoscope_dict = data.get("signes", {})
                signe_data = horoscope_dict.get(signe_detecte.lower())
                if signe_data:
                    horoscope = signe_data.get("horoscope", "Aucun horoscope disponible")
                    return f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {horoscope}\n"
                else:
                    return f"🔍 Horoscope indisponible pour **{signe_detecte.capitalize()}**. Essayez plus tard."
            else:
                return "❌ Impossible d'obtenir l'horoscope pour le moment."
        except Exception as e:
            return f"⚠️ Erreur lors de la récupération de l'horoscope : {e}"

    # --- Météo ---
    if any(kw in question_clean for kw in ["météo", "quel temps"]):
        ville_detectee = "Paris"
        match_geo = re.search(r"(?:à|au|aux|dans|sur|en)\s+([A-Za-zÀ-ÿ' -]+)", question_clean)
        if not match_geo:
            match_geo = re.search(r"m[eé]t[eé]o\s+(.+)$", question_clean)
        if match_geo:
            lieu = match_geo.group(1).strip().rstrip(" ?.!;")
            ville_detectee = lieu.title()
        meteo = get_meteo_ville(ville_detectee)
        if "erreur" in meteo.lower():
            return f"⚠️ Je n'ai pas trouvé la météo pour **{ville_detectee}**. Essayez un autre lieu."
        else:
            return f"🌦️ **Météo à {ville_detectee}** :\n{meteo}"

    # --- Actualités ---
    if "actualité" in question_clean or "news" in question_clean:
        actus = get_general_news()
        if isinstance(actus, str):
            return actus
        elif actus and isinstance(actus, list):
            message = "📰 **Dernières actualités importantes :**\n\n"
            for i, (titre, lien) in enumerate(actus[:5], 1):
                message += f"{i}. 🔹 [{titre}]({lien})\n"
            return message + "\n🧠 *Restez curieux, le savoir, c’est la puissance !*"
        else:
            return "⚠️ Je n’ai pas pu récupérer les actualités pour le moment."

    # --- Analyse simple (commence par analyse ...) ---
    if question_clean.startswith("analyse "):
        nom_simple = question_clean.replace("analyse", "").strip()
        nom_simple_norm = remove_accents(nom_simple)
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
            "cl": "cl=F", "pétrole": "cl=F", "petrole": "cl=F",
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
                        texte += "🔻 **Zone de survente détectée.**\n"
                    if "surachat" in signaux_str:
                        texte += "🔺 **Zone de surachat détectée.**\n"
                    if "haussier" in signaux_str:
                        texte += "📈 **Tendance haussière détectée.**\n"
                    if "baissier" in signaux_str:
                        texte += "📉 **Tendance baissière détectée.**\n"
                    if "faible" in signaux_str:
                        texte += "😴 **Tendance faible.**\n"
                    return texte if texte else "ℹ️ Aucun signal fort détecté."

                signaux = analyse.split("\n") if analyse else []
                resume = generer_resume_signal(signaux)

                return (
                    f"📊 **Analyse pour {nom_simple.upper()}**\n\n"
                    f"{analyse}\n\n"
                    f"💬 **Résumé d'AVA :**\n{resume}\n\n"
                    f"🤖 *Intuition d'AVA :* {suggestion}"
                )
            else:
                return f"⚠️ Je ne trouve pas les données pour {nom_simple.upper()}."
        else:
            return f"🤔 Je ne connais pas encore **{nom_simple}**. Réessayez avec un autre actif."

    # --- Fallback ---
    return "🤖 Je n’ai pas encore de réponse spécifique pour cela, mais je m’améliore chaque jour !"
