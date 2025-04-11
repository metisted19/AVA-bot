import streamlit as st
from streamlit.components.v1 import html
from PIL import Image
import base64

st.set_page_config(page_title="Bienvenue sur AVA", layout="wide")

# --- CSS personnalisé pour fond nuit stylé ---
st.markdown("""
    <style>
        body, .stApp {
            background: linear-gradient(135deg, #0f0f0f 0%, #1c1c1c 100%) !important;
            color: #ffffff !important;
        }
        .title {
            text-align: center;
            font-size: 3.5em;
            font-weight: bold;
            margin-top: 2rem;
            color: #00FFFF;
            text-shadow: 0 0 15px #00FFFF;
        }
        .subtitle {
            text-align: center;
            font-size: 1.3em;
            margin-bottom: 1rem;
            color: #d0d0d0;
        }
        .description {
            text-align: center;
            font-size: 1.1em;
            margin-top: -1rem;
            color: #b0b0b0;
        }
        .button-container {
            display: flex;
            justify-content: center;
            margin-top: 2rem;
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

# --- Logo AVA ---
logo = Image.open("ava_logo.png")
st.image(logo, width=220)

# --- Contenu principal ---
st.markdown('<div class="title">Bienvenue sur AVA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Votre assistante boursière, météo et actualités 24h/24 — toujours connectée, toujours prête 🤖</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Entrez dans une nouvelle ère d'analyse intelligente. AVA vous accompagne avec précision et réactivité à chaque instant.</div>', unsafe_allow_html=True)

# --- Bouton vers Dashboard ---
html("""
    <div class="button-container">
        <a href="/Dashboard" target="_self">
            <button class="enter-button">Entrer dans la plateforme</button>
        </a>
    </div>
""", height=100)

# AVA est de retour en beauté 😎

