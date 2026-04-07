import streamlit as st
import pandas as pd
import requests
import math
import re
import google.generativeai as genai # Nova dependência para o Chat

# --- CONFIGURAÇÃO DO CHAT (CÉREBRO DO MESTRE) ---
# Você deve criar uma API KEY em aistudio.google.com
# E colocá-la nos 'Secrets' do Streamlit Cloud
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    CHAT_DISPONIVEL = True
except:
    CHAT_DISPONIVEL = False

# ... (Mantenha as funções anteriores de Macro e Scorecard) ...

# ═══════════════════════════════════════════════════════════════════════════
# NOVA ABA: CHAT COM O MESTRE DIGITAL
# ═══════════════════════════════════════════════════════════════════════════
def interface_chat():
    st.subheader("💬 O Mestre Digital — Mentor R.E.N.D.A.")
    st.markdown('<p class="chapter-ref">INTERAÇÃO EM TEMPO REAL CONFORME O MÉTODO</p>', unsafe_allow_html=True)
    
    if not CHAT_DISPONIVEL:
        st.warning("⚠️ O Chat requer uma API Key configurada. O Mestre está meditando no momento.")
        return

    # Inicializa o histórico
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá, cultivador. Sou o Mestre Digital. O que deseja entender sobre o seu pomar hoje?"}
        ]

    # Exibe as mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do Usuário
    if prompt := st.chat_input("Pergunte ao Mestre (Ex: Por que Diversificar é importante?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta da IA com Persona do Mestre
        with st.chat_message("assistant"):
            # Contexto do Livro + Persona
            instrucao_mestre = f"Você é o Mestre Digital, mentor do livro 'Método R.E.N.D.A.' de Laerson Endrigo Ely. Responda sempre de forma técnica, empática e fiel aos conceitos de Solo, Raízes, Tronco, Galhos e Frutos. Use o conteúdo do livro para esclarecer dúvidas. Pergunta: {prompt}"
            
            response = model.generate_content(instrucao_mestre)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL ATUALIZADA
# ═══════════════════════════════════════════════════════════════════════════
# ... (Código da Âncora Macro) ...

aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

with aba_a:
    # ... (Seu código do Módulo A) ...
    pass

with aba_c:
    # ... (Seu código do Módulo C) ...
    pass

with aba_chat:
    interface_chat()
