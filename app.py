import streamlit as st
from PIL import Image
import base64

# --- Configuration ---
st.set_page_config(page_title="Accueil AVA", layout="wide")

# --- CSS personnalisé pour un look plus classe ---
st.markdown("""
    <style>
    .title {
        font-size: 2.5em;
        text-align: center;
        color: #00C0FF;
        font-weight: bold;
        margin-bottom: 0.5em;
    }
    .subtitle {
        font-size: 1.2em;
        text-align: center;
        color: #aaa;
    }
    .section {
        border-top: 2px solid #444;
        padding-top: 1.5em;
        margin-top: 2em;
    }
    .logo {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 100px;
        margin-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# --- Affichage du logo ---
try:
    logo = Image.open("ava_logo.png")
    st.image(logo, width=100)
except FileNotFoundError:
    st.warning("Logo 'ava_logo.png' non trouvé. Place-le à la racine ou dans 'pages/'.")

# --- Titre principal ---
st.markdown("<div class='title'>🤖 Bienvenue dans AVA</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>L’intelligence artificielle dédiée à l’analyse boursière et crypto en temps réel</div>", unsafe_allow_html=True)

# --- Section Infos ---
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("📊 Ce que peut faire AVA :")
st.markdown("""
- Détecter des **signaux de trading** avec le RSI, MACD, Bollinger Bands, etc.
- Proposer une **interprétation intelligente** grâce à son moteur d’analyse.
- Afficher des **graphiques dynamiques** (bougies, indicateurs).
- Suivre les principaux actifs : `AAPL`, `TSLA`, `GOOGL`, `BTC-USD`, `ETH-USD`.

Et bientôt… AVA évoluera pour devenir **encore plus autonome**. 🚀
""")

# --- Section Navigation ---
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("🧭 Naviguer dans AVA")
st.markdown("""
- Accédez à l’onglet `Dashboard` pour visualiser les **graphiques en bougies + indicateurs**.
- Consultez `Signaux` pour les **opportunités d’achat/vente détectées**.
- Parlez directement à AVA via le chat dans `Chat_AVA`.

*AVA est en constante évolution… reste connecté !*
""")


