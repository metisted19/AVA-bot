import streamlit as st
from PIL import Image

# Logo AVA
logo_path = "ava_logo.png"

st.set_page_config(
    page_title="AVA 3 - Plateforme d’analyse",
    page_icon=logo_path,
    layout="wide",
)

# Affichage du logo et du titre
col1, col2 = st.columns([1, 6])
with col1:
    st.image(logo_path, width=80)
with col2:
    st.markdown("<h1 style='margin-bottom: 0; color:#4FC3F7;'>Bienvenue sur AVA 3</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:gray;'>Votre plateforme d'analyse prédictive multi-actifs avec IA</p>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar stylée
st.sidebar.image(logo_path, width=100)
st.sidebar.markdown("## Navigation")
st.sidebar.page_link("pages/1_Dashboard.py", label="Dashboard", icon="📊")
st.sidebar.page_link("pages/2_Signaux.py", label="Signaux", icon="⚡")
st.sidebar.page_link("pages/3_Chat_AVA.py", label="Chat AVA", icon="💬")

st.sidebar.markdown("---")
st.sidebar.markdown("Développé par Teddy avec amour et un soupçon d'IA.")

# Message de bienvenue ou instructions
st.success("Utilise le menu de gauche pour explorer les fonctionnalités.")






