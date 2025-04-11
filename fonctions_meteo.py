# fonctions_meteo.py

def obtenir_meteo(ville="Paris"):
    """
    Retourne une météo fictive pour une ville donnée.
    """
    return f"🌤️ Il fait actuellement 22°C à {ville}. Le ciel est dégagé et une légère brise souffle."

def get_meteo_ville(ville):
    """
    Variante plus réaliste avec vérification de ville.
    À remplacer par une vraie API comme OpenWeather plus tard.
    """
    conditions = {
        "paris": "🌧️ Pluie légère et 18°C",
        "marseille": "☀️ Ensoleillé avec 25°C",
        "lyon": "⛅ Nuages épars, 21°C",
        "toulouse": "🌤️ Temps agréable, 23°C",
        "lille": "🌫️ Brouillard le matin, 17°C"
    }

    ville_clean = ville.strip().lower()
    meteo = conditions.get(ville_clean, f"🌍 Je n’ai pas de données précises pour {ville}. Mais il fait sûrement beau quelque part 😄")

    return f"{meteo} à **{ville.title()}**."
