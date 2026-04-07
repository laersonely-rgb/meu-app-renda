import streamlit as st
import pandas as pd
import requests
import math
import re
import google.generativeai as genai
import yfinance as yf
from datetime import date, datetime

# ═══════════════════════════════════════════════════════════════════════════
# ARQUITETURA E ESTÉTICA (FIEL AO LIVRO)
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 ULTIMATE", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11px!important; background-color: #f4f8f5; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .formula-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 0.9rem; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Motor de Captura (O "Coração" do Garimpo) ──────────────────────────────
def parse_br_number(text):
    if not text: return 0.0
    # Remove pontos de milhar e troca vírgula por ponto
    clean = text.replace('.', '').replace(',', '.')
    try: return float(re.sub(r'[^\d.]', '', clean))
    except: return 0.0

def extract_liquidez(text):
    if not text: return 0.0
    text = text.upper()
    mul = 1
    if "BILH" in text: mul = 1_000_000_000
    elif "MILH" in text: mul = 1_000_000
    elif "K" in text: mul = 1_000
    
    val = parse_br_number(text)
    return val * mul if val < 10000 else val # Evita multiplicar o que já é absoluto

def garimpar_texto(texto):
    """Extrai os 9 Campos do PED via Expressões Regulares"""
    dados = {}
    texto = texto.upper()
    
    # Padrões de busca (Regex)
    dados['lpa'] = re.search(r"LPA[\s\S]{0,50}?([-]?\d+,\d+)", texto)
    dados['vpa'] = re.search(r"VPA[\s\S]{0,50}?(\d+,\d+)", texto)
    dados['roe'] = re.search(r"ROE[\s\S]{0,50}?(\d+,\d+)\s*%", texto)
    dados['dy'] = re.search(r"(?:DY|YIELD)[\s\S]{0,50}?(\d+,\d+)\s*%", texto)
    dados['cagr'] = re.search(r"CAGR[\s\S]{0,80}?(\d+,\d+)\s*%", texto)
    dados['liq'] = re.search(r"LIQUIDEZ[\s\S]{0,80}?([\d.,]+(?:\s*(?:MILH|BILH|M|B))?)", texto)
    dados['de'] = re.search(r"(?:D[IÍ]V[\s\S]{0,10}EBITDA|D/E)[\s\S]{0,50}?(\d+,\d+)", texto)

    return {k: v.group(1) if v else None for k, v in dados.items()}

# ═══════════════════════════════════════════════════════════════════════════
# LOGIN E MACRO (G5)
# ═══════════════════════════════════════════════════════════════════════════
SENHA = "RENDA2026"
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave (Pág 324):", type="password")
    if st.button("Validar Semente"):
        if pwd == SENHA: 
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
aba_a, aba_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# --- MÓDULO A: O GARIMPO INDIVIDUAL ---
with aba_a:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.6 - SCORECARD</span>', unsafe_allow_html=True)
    st.subheader("🔬 Protocolo PED - Captura Automática")
    
    col_input, col_manual = st.columns([2, 1])
    
    with col_input:
        txt_ped = st.text_area("COLE AQUI OS DADOS DO INVESTIDOR10/STATUSINVEST:", height=200, 
                               placeholder="Ex: LPA 1,23  VPA 10,45  ROE 15,2%  Liquidez R$ 557,42 Milhões...")
        
    ped_extraido = garimpar_texto(txt_ped) if txt_ped else {}
    
    with col_manual:
        st.write("**Dados Identificados (Confirme):**")
        lpa_final = st.number_input("LPA (R$)", value=parse_br_number(ped_extraido.get('lpa')))
        vpa_final = st.number_input("VPA (R$)", value=parse_br_number(ped_extraido.get('vpa')))
        roe_final = st.number_input("ROE (%)", value=parse_br_number(ped_extraido.get('roe')))
        dy_final = st.number_input("DY (%)", value=parse_br_number(ped_extraido.get('dy')))
        liq_final = st.number_input("Liquidez Diária (R$)", value=extract_liquidez(ped_extraido.get('liq')))
        
    if st.button("🚀 EXECUTAR ANÁLISE SUPREME"):
        st.markdown("---")
        # Cálculos de Graham (Tronco)
        vi = math.sqrt(22.5 * lpa_final * vpa_final) if lpa_final > 0 else 0
        st.success(f"**VALOR INTRÍNSECO (Tronco - Cap 6.5): R$ {vi:.2f}**")
        
        # Protocolo AVA
        if roe_final < 10: st.error("🚨 AVA-1: ROE abaixo do Ke. Risco de Solo Árido.")
        if liq_final < 1000000: st.error(f"🚨 AVA-2: Liquidez de R$ {liq_final:,.2f} é insuficiente.")

# --- MÓDULO C: O GARIMPO DA CARTEIRA ---
with aba_c:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.3 - A VISÃO DO BOSQUE</span>', unsafe_allow_html=True)
    st.subheader("🌲 Captura de Carteira Completa")
    
    txt_carteira = st.text_area("COLE SUA LISTA DE ATIVOS DO INVESTIDOR10/STATUSINVEST:", height=200,
                                placeholder="Ticker | Nome | % | Preço...\nTAEE11  10%  R$ 35,00\nBBAS3  15%  R$ 28,00")
    
    if st.button("⚖️ PROCESSAR BOSQUE"):
        # Busca tickers (4 letras + 1 ou 2 números)
        tickers = re.findall(r"([A-Z]{4}\d{1,2})", txt_carteira.upper())
        # Busca percentuais
        percentuais = re.findall(r"(\d+,\d+|\d+)\s*%", txt_carteira)
        
        if tickers:
            st.write(f"✅ Identificados {len(tickers)} ativos.")
            # Cria DataFrame para o usuário ver
            bosque_df = pd.DataFrame({"Ativo": tickers})
            st.table(bosque_df)
            
            # Cálculo Talmud (Pilar D)
            fiis = len([t for t in tickers if t.endswith("11")])
            acoes = len(tickers) - fiis
            st.info(f"**Análise Talmud (Pág 210):** Você tem {acoes} Árvores (Ações) e {fiis} Terras (FIIs).")
        else:
            st.warning("Nenhum ativo detectado. Tente copiar a tabela completa do site.")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL™ V.102.09 ULTIMATE — A submissão total ao livro.")
