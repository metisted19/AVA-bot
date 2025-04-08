import streamlit as st
from PIL import Image

st.set_page_config(page_title="Accueil AVA", layout="centered")

# Centre et agrandit le logo
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
logo = Image.open("ava_logo.png")
st.image(logo, width=200)  # Tu peux augmenter la taille ici (200 à 300 px par ex.)
st.markdown("</div>", unsafe_allow_html=True)

# Message de bienvenue personnalisé
st.markdown(
    """
    <div style='text-align: center; font-size: 20px; margin-top: 20px;'>
        <strong>Bienvenue sur AVA</strong> 🤖<br>
        Ton assistante d’analyse boursière intelligente 📊<br>
        Explore les marchés, détecte les signaux, discute avec moi… et prends une longueur d'avance 🚀
    </div>
    """,
    unsafe_allow_html=True
)



