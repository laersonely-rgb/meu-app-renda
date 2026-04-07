import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import math
import re
from bs4 import BeautifulSoup
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

# --- 🤖 MOTOR DE EXTRAÇÃO AUTOMÁTICA E INTELIGENTE ---
@st.cache_data(ttl=3600)
def buscar_dados_macro():
    try:
        selic_req = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()
        ipca_req = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()
        selic = float(selic_req[0]['valor'])
        ipca = float(ipca_req[0]['valor'])
        ntnb_backup = (selic - ipca) * 0.6 + ipca
        return selic, ipca, ntnb_backup
    except:
        return 10.50, 4.50, 6.20

def garimpar_texto_fundamentos(texto):
    """Procura padrões numéricos (LPA, VPA, DY) no texto bruto colado."""
    dados = {}
    def extrair_numero(padrao, texto):
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return float(match.group(1).replace('.', '').replace(',', '.'))
        return None

    dados['preco'] = extrair_numero(r'(?:VALOR ATUAL|Cotação|Preço)[\s\S]{0,20}?R\$?\s*([0-9.,]+)', texto)
    dados['lpa'] = extrair_numero(r'LPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['vpa'] = extrair_numero(r'VPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['dy'] = extrair_numero(r'(?:Dividend Yield|DY)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['roe'] = extrair_numero(r'ROE[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['pvp'] = extrair_numero(r'P/VP[\s\S]{0,20}?([0-9.,]+)', texto)
    return dados

def garimpar_carteira_texto(texto):
    """Lê o texto do consolidador, acha o Ticker e a Porcentagem na mesma linha ou nas próximas."""
    linhas = texto.upper().split('\n')
    carteira_dict = {}
    
    for i, linha in enumerate(linhas):
        # 1. Procura um Ticker
        ticker_match = re.search(r'\b([A-Z]{4}[1-9]{1,2})\b', linha)
        if ticker_match:
            ticker = ticker_match.group(1)
            peso = None
            
            # 2. Procura a porcentagem (%) na mesma linha
            peso_match = re.search(r'(\d+[.,]\d+|\d+)\s*%', linha)
            
            # 3. Se não achar, procura nas próximas 3 linhas (tabelas copiadas quebram linha)
            if not peso_match:
                for j in range(1, 4):
                    if i + j < len(linhas):
                        peso_match = re.search(r'(\d+[.,]\d+|\d+)\s*%', linhas[i+j])
                        if peso_match:
                            break
            
            if peso_match:
                peso = float(peso_match.group(1).replace(',', '.'))
            else:
                peso = 0.0
                
            # Salva no dicionário (atualiza se achar repetido com peso maior)
            if ticker not in carteira_dict or peso > carteira_dict[ticker]:
                carteira_dict[ticker] = peso

    # Converte para a lista da tabela
    lista_final = []
    for t, p in carteira_dict.items():
        tipo = "AÇÕES" if t.endswith(('3', '4', '5', '6')) else "FIIs"
        lista_final.append({"Ticker": t, "% Cart": p, "Tipo": tipo, "DY (%)": 0.0})
    
    # Normalização de segurança (Se o consolidador não copiou os %, dividimos igual)
    if lista_final:
        soma_pesos = sum([item["% Cart"] for item in lista_final])
        if soma_pesos == 0:
            peso_igual = round(100.0 / len(lista_final), 2)
            for item in lista_final: item["% Cart"] = peso_igual
        elif abs(soma_pesos - 100) > 2.0:
            # Re-calcula para fechar 100% perfeitamente
            for item in lista_final:
                item["% Cart"] = round((item["% Cart"] / soma_pesos) * 100, 2)
                
    return lista_final

# --- EXECUÇÃO PRINCIPAL ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    
    with st.expander("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO (Automático BCB)", expanded=True):
        selic_auto, ipca_auto, ntnb_auto = buscar_dados_macro()
        c1, c2, c3 = st.columns(3)
        selic = c1.number_input("Selic Meta (%)", value=float(selic_auto))
        ipca = c2.number_input("IPCA 12m (%)", value=float(ipca_auto))
        ntnb = c3.number_input("NTN-B Longa (IPCA + %)", value=float(ntnb_auto))

    aba_a, aba_c = st.tabs(["🌳 Módulo A: Análise Individual", "🌲 Módulo C: Visão do Bosque (Carteira)"])

    # =====================================================================
    # ABA 1: MÓDULO A
    # =====================================================================
    with aba_a:
        st.subheader("🔬 PROTOCOLO DE EXTRAÇÃO DETERMINÍSTICO (PED)")
        c_tick, c_tipo = st.columns([1, 2])
        ticker = c_tick.text_input("Ticker do Ativo:").upper()
        tipo_ativo = c_tipo.radio("Natureza do Ativo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"], horizontal=True)

        with st.expander("📥 PREENCHIMENTO AUTOMÁTICO VIA TEXTO (Copiar/Colar)"):
            st.info("Aperte CTRL+A na página do ativo no Investidor10, CTRL+C e cole abaixo.")
            texto_colado = st.text_area("Cola aqui o texto da página do ativo:", height=100)
            dados_garimpados = garimpar_texto_fundamentos(texto_colado) if texto_colado else {}
            if dados_garimpados: st.success("✅ Campos preenchidos automaticamente!")

        cA, cB, cC = st.columns(3)
        with cA:
            preco = st.number_input("Preço Atual (R$)", value=float(dados_garimpados.get('preco') or 10.0))
            lpa = st.number_input("Campo 1: LPA (R$)", value=float(dados_garimpados.get('lpa') or 1.0)) if tipo_ativo == "AÇÕES" else 0
            vpa = st.number_input("Campo 2: VPA (R$)", value=float(dados_garimpados.get('vpa') or 10.0))
            dy = st.number_input("Campo 3: DY 12m (%)", value=float(dados_garimpados.get('dy') or 6.0))
        with cB:
            cagr = st.number_input("Campo 7: CAGR Div. 3 anos (%)", value=5.0)
            liquidez = st.number_input("Campo 6: Liquidez Diária (R$ Mil)", value=5000.0)
            if tipo_ativo == "AÇÕES":
                roe = st.number_input("Campo 4: ROE (%)", value=float(dados_garimpados.get('roe') or 15.0))
                div_ebitda = st.number_input("Campo 5: Dívida Líq / EBITDA", value=1.5)
            elif tipo_ativo == "FII TIJOLO":
                vacancia = st.number_input("Campo 9A: Vacância (%)", value=4.0)
                ltv = st.number_input("Campo 5: LTV (%)", value=15.0)
            elif tipo_ativo == "FII PAPEL":
                inadimplencia = st.number_input("Campo 9B: Inadimplência (%)", value=0.5)
        with cC:
            if tipo_ativo == "AÇÕES":
                setor = st.selectbox("Pilar E - Setor:", ["Essencial Perene", "Essencial Moderado", "Semi-Essencial", "Cíclico"])
                tendencia = st.selectbox("Campo 9C: Tendência Lucros:", ["Crescente", "Estável", "Decrescente 3 anos", "Prejuízo Recorrente"])
            elif tipo_ativo == "FII TIJOLO":
                setor = st.selectbox("Pilar E - Segmento:", ["Tijolo Essencial", "Tijolo Misto", "Tijolo Cíclico"])
            elif tipo_ativo == "FII PAPEL":
                setor = st.selectbox("Pilar E - Lastro:", ["CRI Setores Essenciais", "CRI Diversificado"])

        if st.button("Executar Scorecard R.E.N.D.A."):
            notas, diag = {}, {}
            if cagr > 10: notas['R'] = 20
            elif cagr > 5: notas['R'] = 15
            elif cagr > 0: notas['R'] = 10
            else: notas['R'] = 5
            diag['R'] = f"CAGR: {cagr}%"

            notas['E'] = 20 if "Essencial" in setor and "Semi" not in setor else 15 if "Moderado" in setor or "Misto" in setor else
