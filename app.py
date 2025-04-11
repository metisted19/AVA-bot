import streamlit as st
from PIL import Image

st.set_page_config(page_title="Bienvenue sur AVA", layout="wide")

# --- CSS personnalisé pour fond nuit stylé ---
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            background: linear-gradient(135deg, #0a0a0a, #1e1e1e) !important;
            color: white !important;
        }
        .title {
            text-align: center;
            font-size: 3.5em;
            font-weight: bold;
            margin-top: 2rem;
            color: #00FFFF;
            text-shadow: 0 0 20px #00FFFF;
        }
        .subtitle {
            text-align: center;
            font-size: 1.4em;
            margin-bottom: 2rem;
            color: #CCCCCC;
        }
        .button-container {
            display: flex;
            justify-content: center;
            margin-top: 3rem;
        }
        .enter-button {
            background-color: #00FFFF;
            color: #000000;
            border: none;
            padding: 1rem 2.5rem;
            font-size: 1.3em;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 0 20px #00FFFF;
            transition: 0.3s ease;
        }
        .enter-button:hover {
            background-color: #00cccc;
            box-shadow: 0 0 25px #00cccc;
        }
    </style>
""", unsafe_allow_html=True)

# --- Contenu principal ---
st.markdown('<div class="title">Bienvenue sur AVA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Votre assistante boursière, météo et actualités 24h/24 — toujours connectée, toujours prête 🤖</div>', unsafe_allow_html=True)

# --- Logo AVA local centré ---
logo = Image.open("assets/ava_logo.png")
st.image(logo, width=220)

# --- Bouton vers Dashboard (corrigé sans html) ---
st.markdown("""
    <div class="button-container">
        <a href="/Dashboard" target="_self">
            <button class="enter-button">Entrer dans la plateforme</button>
        </a>
    </div>
""", unsafe_allow_html=True)

# AVA est de retour en beauté 😎
