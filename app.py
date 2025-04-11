import streamlit as st
from PIL import Image
import time

# --- Configuration de la page ---
st.set_page_config(page_title="Bienvenue sur AVA", layout="centered")

# --- Logo ---
logo = Image.open("ava_logo.png")
st.image(logo, width=150)

# --- Titre stylisé ---
st.markdown("""
<style>
.big-title {
    font-size: 36px;
    text-align: center;
    font-weight: bold;
    color: #10a37f;
    margin-bottom: 20px;
}
.subtext {
    text-align: center;
    font-size: 20px;
    color: #999;
    margin-bottom: 40px;
}
.button-style {
    display: flex;
    justify-content: center;
    gap: 40px;
}
.stButton>button {
    font-size: 18px !important;
    padding: 0.6em 1.5em !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>Bienvenue sur AVA</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>L'intelligence artificielle boursière autonome, évolutive et prête à vous guider.</div>", unsafe_allow_html=True)

# --- Boutons de navigation ---
st.markdown("<div class='button-style'>", unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("💬 Accéder au Chat"):
        st.switch_page("pages/3_Chat_AVA.py")

with col2:
    if st.button("📈 Ouvrir le Dashboard"):
        st.switch_page("pages/1_Dashboard.py")

st.markdown("</div>", unsafe_allow_html=True)

# --- Bas de page ---
st.markdown("""
---
<center><sub>Développé avec ❤️ par Teddy & AVA</sub></center>
""")






