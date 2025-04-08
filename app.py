import streamlit as st

# --- Configuration de la page ---
st.set_page_config(page_title="Accueil AVA", layout="centered")

# --- Logo centré ---
st.markdown("""
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/metisted19/AVA-bot/master/ava_logo.png" width="140">
    </div>
""", unsafe_allow_html=True)

# --- Titre et description stylisée ---
st.markdown("""
    <div style="text-align: center; margin-top: 30px;">
        <h1 style="color: #4A90E2;">Bienvenue sur AVA</h1>
        <p style="font-size: 18px;">
            Votre assistante boursière intelligente 🔍💼<br><br>
            Analyse technique, signaux puissants, conversations futuristes : AVA vous guide sur les marchés avec précision, style et bonne humeur 🚀<br><br>
            Explorez les différentes sections dans le menu à gauche 👈
        </p>
    </div>
""", unsafe_allow_html=True)




