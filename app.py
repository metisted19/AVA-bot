import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Bienvenue sur AVA", layout="wide")

# --- CSS personnalisé pour fond nuit stylé ---
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            background: linear-gradient(135deg, #0f0f0f 0%, #1c1c1c 100%) !important;
            color: white !important;
        }
        .title {
            text-align: center;
            font-size: 4em;
            font-weight: bold;
            margin-top: 4rem;
            color: #00FFFF;
            text-shadow: 0 0 20px #00FFFF;
        }
        .subtitle {
            text-align: center;
            font-size: 1.4em;
            margin-bottom: 3rem;
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

# --- Bouton vers Dashboard ---
html("""
    <div class="button-container">
        <a href="/Dashboard" target="_self">
            <button class="enter-button">Entrer dans la plateforme</button>
        </a>
    </div>
""", height=100)

# TODO : ajouter logo ou animation futuriste plus tard





