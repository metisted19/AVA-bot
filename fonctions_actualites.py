# fonctions_actualites.py

import requests

def obtenir_actualites():
    """
    Fonction simple simulant une récupération d'actualités économiques (peut être remplacée par une API plus tard).
    """
    return [
        ("Les marchés financiers commencent la journée en hausse", "https://www.lemonde.fr/economie/"),
        ("La BCE annonce une décision importante sur les taux", "https://www.lesechos.fr/finance-marches/")
    ]

def get_general_news():
    """
    Simule un flux d'actualités générales (à relier à NewsAPI ou autre si besoin).
    """
    return [
        ("Le climat économique mondial évolue rapidement", "https://www.francetvinfo.fr/economie/"),
        ("Nouvelles réglementations sur les crypto-actifs en Europe", "https://www.bfmtv.com/economie/")
    ]
