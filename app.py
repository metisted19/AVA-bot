import streamlit as st
import base64

# --- Configuration de la page ---
st.set_page_config(page_title="Accueil AVA", layout="centered")

# --- Image logo centrée ---
st.image("ava_logo.png", width=150)

# --- Titre stylé ---
st.markdown("""
    <h1 style='text-align: center; font-size: 3em; color: #6C63FF;'>Bienvenue sur AVA</h1>
    <p style='text-align: center; font-size: 1.2em;'>L'intelligence artificielle boursière autonome, à votre service 24h/24.</p>
""", unsafe_allow_html=True)

# --- Animation d'intro (texte déroulant ou effet cool) ---
st.markdown("""
    <style>
    .fade-in {
        animation: fadeIn 2s ease-in;
    }
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    </style>
    <div class="fade-in" style='text-align: center; padding: 30px;'>
        <p style='font-size: 1.1em;'>Prédictions, analyses techniques, actualités, météo... AVA ne dort jamais.</p>
    </div>
""", unsafe_allow_html=True)

# --- Boutons vers les fonctionnalités ---
st.markdown("""
    <div style='text-align: center;'>
        <a href='/1_Dashboard' style='text-decoration: none;'>
            <button style='margin: 10px; padding: 10px 25px; font-size: 1em; border-radius: 12px; background-color: #6C63FF; color: white; border: none;'>📈 Dashboard</button>
        </a>
        <a href='/2_Signaux' style='text-decoration: none;'>
            <button style='margin: 10px; padding: 10px 25px; font-size: 1em; border-radius: 12px; background-color: #6C63FF; color: white; border: none;'>📊 Signaux</button>
        </a>
        <a href='/3_Chat_AVA' style='text-decoration: none;'>
            <button style='margin: 10px; padding: 10px 25px; font-size: 1em; border-radius: 12px; background-color: #6C63FF; color: white; border: none;'>💬 Chat AVA</button>
        </a>
    </div>
""", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
    <hr>
    <p style='text-align: center; font-size: 0.8em; color: gray;'>© 2025 AVA Technologies. Projet de Teddy & ChatGPT 🤖</p>
""", unsafe_allow_html=True)






