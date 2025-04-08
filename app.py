import streamlit as st

st.set_page_config(page_title="Bienvenue sur AVA", layout="centered")

# Style CSS personnalisé
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .ava-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }
    .intro-texte {
        text-align: center;
        font-size: 20px;
        font-weight: 500;
        color: #555;
        margin-top: -20px;
    }
    </style>
""", unsafe_allow_html=True)

# Affichage du logo centré
st.markdown('<div class="ava-logo"><img src="ava_logo.png" width="160"></div>', unsafe_allow_html=True)

# Phrase d’accroche
st.markdown('<div class="intro-texte">Bienvenue sur AVA, votre assistante boursière intelligente 🔍💼</div>', unsafe_allow_html=True)




