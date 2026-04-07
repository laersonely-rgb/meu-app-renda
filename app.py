import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import math
from datetime import date

st.set_page_config(page_title="Método R.E.N.D.A. V.102.09", layout="wide")

# --- MÓDULO 0: AVISO LEGAL ---
def exibir_aviso_legal():
    st.code("""
+----------------------------------------------------------------------+
|  ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|  Exercício estritamente educacional e matemático.                    |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
+----------------------------------------------------------------------+
    """, language="text")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.title("🔐 Acesso ao Mestre Digital")
        pwd = st.text_input("Chave de Acesso:", type="password")
        if st.button("Validar Semente"):
            if pwd == "RENDA2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
        return False
    return True

# --- EXTRATORES AUTOMÁTICOS ---
@st.cache_data(ttl=3600)
def buscar_dados_macro():
    try:
        # Selic via API do Banco Central (SGS 1178)
        selic_req = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados/ultimos/1").json()
        selic = float(selic_req[0]['valor'])
        # IPCA via API do Banco Central (SGS 433 - aproximação simplificada do último mês x 12)
        ipca_req = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/12").json()
        ipca = sum([float(mes['valor']) for mes in ipca_req])
        return selic, ipca
    except:
        return 10.50, 4.50 # Fallback de segurança

@st.cache_data(ttl=3600)
def extrair_investidor10(ticker):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = f"https://investidor10.com.br/acoes/{ticker.lower()}/"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extração genérica (pode falhar se o site mudar o layout)
            dy = soup.find('div', title='Dividend Yield').find('div', class_='value').text
            pvp = soup.find('div', title='P/VP').find('div', class_='value').text
            return {"dy": float(dy.replace('%','').replace(',','.')), "pvp": float(pvp.replace(',','.'))}
        return None
    except:
        return None

# --- EXECUÇÃO PRINCIPAL ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    
    # 🌐 MÓDULO MACRO AUTOMÁTICO
    st.subheader("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO")
    selic_auto, ipca_auto = buscar_dados_macro()
    c1, c2, c3 = st.columns(3)
    selic = c1.number_input("Selic Meta (%)", value=selic_auto)
    ipca = c2.number_input("IPCA 12m (%)", value=ipca_auto)
    ntnb = c3.number_input("NTN-B Longa (IPCA + %)", value=6.20)
    
    st.markdown("---")
    
    # 🔬 MÓDULO DE EXTRAÇÃO DO ATIVO
    ticker = st.text_input("Ticker do Ativo (ex: BBAS3, HGLG11):").upper()
    tipo_ativo = st.radio("Selecione a Natureza do Ativo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"], horizontal=True)

    if ticker:
        with st.spinner(f"A conectar com o Investidor10 para extrair {ticker}..."):
            dados_i10 = extrair_investidor10(ticker)
            
            if dados_i10:
                st.success("✅ Conexão com Investidor10 estabelecida com sucesso!")
                dy_default = dados_i10.get('dy', 6.0)
                pvp_default = dados_i10.get('pvp', 1.0)
            else:
                st.warning("⚠️ O Investidor10 bloqueou a extração automática (Proteção Cloudflare). Ativando Modo de Auditoria Manual.")
                dy_default = 6.0
                pvp_default = 1.0

        st.write("Confirme os fundamentos da empresa:")
        colA, colB, colC = st.columns(3)
        with colA:
            preco = st.number_input("Preço Atual (R$)", value=10.0)
            lpa = st.number_input("LPA (R$)", value=1.0) if tipo_ativo == "AÇÕES" else 0
            vpa = st.number_input("VPA (R$)", value=10.0)
        with colB:
            dy = st.number_input("DY 12m (%)", value=dy_default)
            cagr = st.number_input("CAGR Div. 3 anos (%)", value=5.0)
            if tipo_ativo == "AÇÕES": roe = st.number_input("ROE (%)", value=15.0)
        with colC:
            if tipo_ativo == "AÇÕES": setor = st.selectbox("Setor (Essenciais):", ["Essencial Perene", "Essencial Moderado", "Semi-Essencial", "Cíclico"])
            elif tipo_ativo == "FII TIJOLO": setor = st.selectbox("Setor (FII):", ["Tijolo Essencial", "Tijolo Misto", "Tijolo Cíclico"])
            else: setor = "Papel/CRI"

        if st.button("Gerar Scorecard R.E.N.D.A."):
            notas = {}
            diag = {}

            # PILAR R - REINVESTIMENTO
            if cagr > 10: notas['R'] = 20
            elif cagr > 5: notas['R'] = 15
            else: notas['R'] = 5
            diag['R'] = f"CAGR: {cagr}%"

            # PILAR E - ESSENCIAIS
            notas['E'] = 20 if "Essencial" in setor else 10
            diag['E'] = setor

            # PILAR N - NEGÓCIOS SÓLIDOS
            if tipo_ativo == "AÇÕES":
                notas['N'] = 20 if roe > 15 else 10
                diag['N'] = f"ROE: {roe}%"
            else:
                notas['N'] = 15
                diag['N'] = "Análise de Fundos"

            # PILAR A - ALOCAÇÃO
            if tipo_ativo == "AÇÕES":
                if lpa > 0 and vpa > 0:
                    vi = math.sqrt(22.5 * lpa * vpa)
                    margem = ((vi - preco) / vi) * 100
                    notas['A'] = 20 if margem > 20 else 10
                    diag['A'] = f"Margem: {margem:.1f}%"
            else:
                notas['A'] = 20 if (preco/vpa) < 1 else 10
                diag['A'] = "P/VP Recalculado"

            # Tabela SCORECARD com R.E.N.D.A.
            st.markdown(f"### 📊 MÓDULO 8 — SCORECARD R.E.N.D.A. ({ticker})")
            
            df = pd.DataFrame({
                "Pilar": ["R (Reinvestimento)", "E (Essenciais)", "N (Negócios Sólidos)", "D (Diversificação)", "A (Alocação)"],
                "Nota (0-20)": [notas.get('R'), notas.get('E'), notas.get('N'), "N/A (Módulo C)", notas.get('A')],
                "Diagnóstico": [diag.get('R'), diag.get('E'), diag.get('N'), "Exclusivo Carteira", diag.get('A')]
            })
            
            st.table(df)
