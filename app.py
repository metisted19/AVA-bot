import streamlit as st

st.set_page_config(page_title="Accueil AVA", layout="centered")

st.markdown("""
<style>
h1 {
    font-size: 60px;
    color: #10cfc9;
    text-align: center;
    font-weight: bold;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-top: 2rem;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    text-shadow: 0 0 10px #10cfc9, 0 0 20px #10cfc9;
  }
  to {
    text-shadow: 0 0 20px #0fa, 0 0 30px #0fa;
  }
}

p.description {
    font-size: 20px;
    text-align: center;
    margin-top: 2rem;
    color: #ffffff;
    font-style: italic;
}

.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: 3rem;
    border-radius: 20px;
    box-shadow: 0 0 30px rgba(0,255,255,0.3);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1>AVA</h1>
<p class="description">Votre intelligence boursière évolutive, à votre service 24h/24.</p>
""", unsafe_allow_html=True)

st.image("ava_logo.png", width=200)

st.markdown("""
<div style="text-align:center; margin-top:2rem;">
    <a href="/1_Dashboard" target="_self" style="font-size: 18px; color: #10cfc9;">📊 Accéder au Dashboard</a>
    <br><br>
    <a href="/2_Signaux" target="_self" style="font-size: 18px; color: #10cfc9;">📈 Voir les Signaux</a>
    <br><br>
    <a href="/3_Chat_AVA" target="_self" style="font-size: 18px; color: #10cfc9;">💬 Ouvrir le Chat AVA</a>
</div>
""", unsafe_allow_html=True)





