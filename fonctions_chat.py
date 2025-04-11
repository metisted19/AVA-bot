# fonctions_chat.py

def obtenir_reponse_ava(question):
    """
    Répond de façon générique si aucune analyse spécifique n'est déclenchée.
    Vous pouvez enrichir cette fonction avec une logique NLP plus avancée.
    """
    question = question.lower()

    if "blague" in question:
        return "Pourquoi les programmeurs n’aiment-ils pas sortir ? Parce qu’ils ont trop de bugs à corriger ! 😄"

    elif "motivation" in question:
        return "🔥 Continuez d’avancer, les étoiles ne sont qu’à quelques lignes de code !"

    elif "futur" in question:
        return "Le futur est déjà là. Il suffit de savoir le coder."

    else:
        return "Je suis AVA, votre assistante IA. Posez-moi une question sur la bourse, la météo ou les actualités ! 😊"
