import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
import google.generativeai as genai
from datetime import date, datetime

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÃO DE ENGENHARIA SUPREME
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 SUPREME", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11px!important; background-color: #f4f8f5; border: 1px solid #c8e6c9; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .formula-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 0.9rem; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Configuração IA (Mestre Digital) ──────────────────────────────────────
# Corrigindo o erro NotFound: Garantindo o ID correto do modelo
CHAT_OK = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 'gemini-1.5-flash' é o nome oficial e estável
        chat_model = genai.GenerativeModel('gemini-1.5-flash')
        CHAT_OK = True
    except Exception as e:
        st.sidebar.error(f"Erro ao ligar o Mestre: {e}")

# ── Globais e Segurança ───────────────────────────────────────────────────
SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 SUPREME               |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
+----------------------------------------------------------------------+"""

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ═══════════════════════════════════════════════════════════════════════════
# 2. MOTORES DE CÁLCULO E EXTRAÇÃO (GARIMPADEIRO)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        r_s = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=8).json()[0]["valor"]
        r_i = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=8).json()[0]["valor"]
        selic, ipca = float(r_s), float(r_i)
    except:
        selic, ipca = 10.75, 4.50
    
    dias = max(0, (date.today() - date(2026, 1, 29)).days)
    copom_min = 276 + int(dias / 45)
    ntnb = round((selic - ipca) * 0.6 + ipca, 2)
    return {"selic": selic, "ipca": ipca, "ntnb": ntnb, "copom_min": copom_min}

def garimpar_ped(texto):
    t = texto.upper()
    def _find(p):
        m = re.search(p, t)
        if m:
            val = m.group(1).replace(".", "").replace(",", ".")
            try: return float(val)
            except: return 0.0
        return 0.0

    return {
        "lpa": _find(r"LPA[\s\S]{0,50}?([-]?\d+[,.]\d+)"),
        "vpa": _find(r"VPA[\s\S]{0,50}?(\d+[,.]\d+)"),
        "dy": _find(r"(?:YIELD|DY)[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "roe": _find(r"ROE[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "de": _find(r"D[IÍ]V[\s\S]{0,15}?EBITDA[\s\S]{0,30}?(\d+[,.]\d+)"),
        "cagr": _find(r"CAGR[\s\S]{0,30}?(?:DPA|DIVIDENDO)[\s\S]{0,20}?(\d+[,.]\d+)\s*%"),
    }

# ═══════════════════════════════════════════════════════════════════════════
# 3. TELA DE ACESSO
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso (Pág 324):", type="password")
    if st.button("Validar Semente"):
        if pwd.strip().upper() == SENHA:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Chave inválida.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# 4. INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
MA = fetch_macro()
st.code(AVISO_LEGAL, language="text")

# --- ÂNCORA MACRO ---
st.markdown('<span class="chapter-tag">CAPÍTULO 5.2 - O CLIMA MACRO</span>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
selic_ui = c1.number_input("Selic (%)", value=MA["selic"])
ipca_ui = c2.number_input("IPCA (%)", value=MA["ipca"])
juro_real = selic_ui - ipca_ui
clima = "❄️ INVERNO" if juro_real > 10 else "☀️ VERÃO"
st.info(f"**Juro Real: {juro_real:.2f}% | Clima: {clima} MACRO**")

aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

# --- MÓDULO A: GARIMPO E AUTO-FILL ---
with aba_a:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.6 - SCORECARD</span>', unsafe_allow_html=True)
    tk = st.text_input("TICKER:", placeholder="Ex: BBAS3").upper().strip()
    
    if tk:
        txt_ped = st.text_area("COLE OS INDICADORES DO INVESTIDOR10 AQUI:", height=150, key=f"area_{tk}")
        
        # O GARIMPO acontece agora
        ped = garimpar_ped(txt_ped) if txt_ped else {}
        
        with st.expander("📝 Auditoria de Campos (Auto-fill)", expanded=True):
            st.caption("Os valores abaixo são extraídos automaticamente do texto acima.")
            f1, f2, f3, f4 = st.columns(4)
            # Usando KEY dinâmica para garantir que o Streamlit atualize as caixas ao colar o texto
            lpa_v = f1.number_input("LPA (R$)", value=ped.get("lpa", 0.0), format="%.4f", key=f"lpa_{tk}_{len(txt_ped)}")
            vpa_v = f1.number_input("VPA (R$)", value=ped.get("vpa", 0.0), format="%.4f", key=f"vpa_{tk}_{len(txt_ped)}")
            dy_v = f2.number_input("DY (%)", value=ped.get("dy", 0.0), key=f"dy_{tk}_{len(txt_ped)}")
            roe_v = f2.number_input("ROE (%)", value=ped.get("roe", 0.0), key=f"roe_{tk}_{len(txt_ped)}")
            de_v = f3.number_input("D/EBITDA", value=ped.get("de", 0.0), key=f"de_{tk}_{len(txt_ped)}")
            cagr_v = f3.number_input("CAGR (%)", value=ped.get("cagr", 0.0), key=f"cagr_{tk}_{len(txt_ped)}")
            prc_v = f4.number_input("Preço Atual (R$)", value=10.0, key=f"prc_{tk}")

        if st.button("🚀 EXECUTAR ANÁLISE"):
            vi = math.sqrt(22.5 * lpa_v * vpa_v) if lpa_v > 0 else 0
            st.success(f"**Valor Intrínseco (Tronco - Cap 6.5): R$ {vi:.2f}**")
            if roe_v < selic_ui:
                st.markdown(f'<div class="veto-alert">🚨 AVA-1: ROE {roe_v}% menor que Ke {selic_ui}%. Destruição de valor.</div>', unsafe_allow_html=True)

# --- MÓDULO C: CARTEIRA ---
with aba_c:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.3 - ALOCAÇÃO</span>', unsafe_allow_html=True)
    st.info("Em breve: Análise C.0 a C.11 completa.")

# --- MÓDULO CHAT: O MESTRE DIGITAL ---
with aba_chat:
    st.subheader("💬 Fale com o Mestre Digital")
    if CHAT_OK:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Olá, cultivador. Estamos em um {clima} MACRO (Juro Real de {juro_real:.2f}%). Como posso ajudar seu pomar?"}]
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        if prompt := st.chat_input("Pergunte algo..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    # Injetando contexto do livro na IA para evitar alucinação
                    contexto = f"Você é o Mestre Digital do livro Método R.E.N.D.A de Laerson Ely. Use terminologia botânica. O clima macro atual é {clima} com juro real de {juro_real}%. Pergunta: {prompt}"
                    response = chat_model.generate_content(contexto)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"O Mestre está meditando. Erro: {e}")
    else:
        st.error("Configure a API Key no Streamlit para usar o Chat.")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL™ V.102.09 SUPREME © 2026 Laerson Ely")
