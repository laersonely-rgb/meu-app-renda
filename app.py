import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
import google.generativeai as genai
from datetime import date, datetime

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÃO DE ENGENHARIA E ESTÉTICA (FIEL AO LIVRO)
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 SUPREME", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11px!important; background-color: #f4f8f5; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; display: inline-block; }
    .formula-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 0.9rem; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; }
    .ok-box{background:#00c85322;border-left:4px solid #00c853;padding:.6rem 1rem;border-radius:4px;margin:.4rem 0}
</style>
""", unsafe_allow_html=True)

# ── Configuração IA (Mestre Digital) ──────────────────────────────────────
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    chat_model = genai.GenerativeModel('gemini-1.5-flash')
    CHAT_OK = True
else:
    CHAT_OK = False

# ── Globais e Segurança ───────────────────────────────────────────────────
SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 SUPREME               |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
+----------------------------------------------------------------------+"""

# ═══════════════════════════════════════════════════════════════════════════
# 2. MOTORES DE CÁLCULO E EXTRAÇÃO (ORIGINAIS PRESERVADOS)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_macro():
    now = datetime.now().strftime("%d/%m %H:%M")
    try:
        r_s = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=8).json()[0]["valor"]
        r_i = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=8).json()[0]["valor"]
        selic, ipca = float(r_s), float(r_i)
        src = "BCB API"
    except:
        selic, ipca, src = 10.75, 4.50, "FALLBACK"
    
    dias = max(0, (date.today() - date(2026, 1, 29)).days)
    copom_min = 276 + int(dias / 45)
    ntnb = round((selic - ipca) * 0.6 + ipca, 2)
    return {"selic": selic, "ipca": ipca, "ntnb": ntnb, "copom_min": copom_min, "now": now, "src": src}

def fmt_ancora(m, copom):
    ok = "OK" if copom >= m["copom_min"] else "OBSOLETO"
    return f"""\
+---------------+-----------+------------------+--------------+------------------+
| Variavel      | Valor     | Fonte            | Data/Hora    | Prova Sombra     |
+---------------+-----------+------------------+--------------+------------------+
| Selic Meta    | {m['selic']:>7.2f}% | {m['src']:<16} | {m['now']:<12} | COPOM {copom} {ok} |
| IPCA 12m      | {m['ipca']:>7.2f}% | BCB/IBGE         | {m['now']:<12} | [Mes recente]    |
| NTN-B Longa   |IPCA+{m['ntnb']:.2f}% | Calculado        | {m['now']:<12} | [Regra D-1]      |
+---------------+-----------+------------------+--------------+------------------+"""

def garimpar_ped(texto):
    t = texto.upper()
    def _fnum(padrao):
        m = re.search(padrao, t, re.I | re.DOTALL)
        if not m: return 0.0
        raw = m.group(1).replace(".", "").replace(",", ".")
        try: return float(raw)
        except: return 0.0

    m_liq = re.search(r"LIQUIDEZ[\s\S]{0,80}?(R?\$?\s*[\d]+[,.][\d]+(?:MILH|BILH|K)?)", t)
    return {
        "lpa": _fnum(r"LPA[\s\S]{0,50}?([-]?[\d]+[,.][\d]+)"),
        "vpa": _fnum(r"VPA[\s\S]{0,50}?([\d]+[,.][\d]+)"),
        "dy": _fnum(r"(?:YIELD|DY)[\s\S]{0,40}?([\d]+[,.][\d]+)\s*%"),
        "roe": _fnum(r"ROE[\s\S]{0,40}?([\d]+[,.][\d]+)\s*%"),
        "de": _fnum(r"D[IÍ]V[\s\S]{0,15}?EBITDA[\s\S]{0,30}?([\d]+[,.][\d]+)"),
        "cagr": _fnum(r"CAGR[\s\S]{0,30}?(?:DPA|DIVIDENDO)[\s\S]{0,20}?([\d]+[,.][\d]+)\s*%"),
        "liq_raw": m_liq.group(1) if m_liq else ""
    }

def parse_liquidez(raw):
    if not raw: return 0.0
    s = str(raw).strip().upper()
    mul = 1
    if "BILH" in s: mul = 1_000_000_000
    elif "MILH" in s: mul = 1_000_000
    elif "K" in s: mul = 1_000
    num = re.sub(r"[^\d,\.]", "", s).replace(".", "").replace(",", ".")
    try: return float(num) * mul if float(num) < 1000000 else float(num)
    except: return 0.0

# ═══════════════════════════════════════════════════════════════════════════
# 3. INTERFACE DE ACESSO
# ═══════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

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
# 4. INTERFACE PRINCIPAL (APÓS LOGIN)
# ═══════════════════════════════════════════════════════════════════════════
st.code(AVISO_LEGAL, language="text")
MA = fetch_macro()

st.markdown('<span class="chapter-tag">CAPÍTULO 5.2 - O CLIMA MACRO</span>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
s_ui = c1.number_input("Selic (%)", value=MA["selic"])
i_ui = c2.number_input("IPCA (%)", value=MA["ipca"])
cp_ui = c3.number_input("Nº COPOM", value=MA["copom_min"])
nb_ui = c4.number_input("NTN-B IPCA+", value=MA["ntnb"])

st.code(fmt_ancora(MA, cp_ui), language="text")

aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

# --- MÓDULO A: GARIMPO COM AUTO-FILL ---
with aba_a:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.6 - SCORECARD</span>', unsafe_allow_html=True)
    tk = st.text_input("TICKER:", placeholder="Ex: BBAS3").upper().strip()
    
    if tk:
        txt_ped = st.text_area("COLE OS INDICADORES DO INVESTIDOR10 AQUI:", height=150)
        
        # A MÁGICA: Garimpar ANTES de mostrar as caixas
        ped = garimpar_ped(txt_ped) if txt_ped else {}
        
        with st.expander("📝 Auditoria e Correção Manual", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            lpa_v = f1.number_input("LPA (R$)", value=ped.get("lpa", 0.0), format="%.4f")
            vpa_v = f1.number_input("VPA (R$)", value=ped.get("vpa", 0.0), format="%.4f")
            dy_v = f2.number_input("DY (%)", value=ped.get("dy", 0.0))
            roe_v = f2.number_input("ROE (%)", value=ped.get("roe", 0.0))
            de_v = f3.number_input("D/EBITDA", value=ped.get("de", 0.0))
            cagr_v = f3.number_input("CAGR (%)", value=ped.get("cagr", 0.0))
            liq_s = f4.text_input("Liquidez:", value=ped.get("liq_raw", ""))
            prc_v = f4.number_input("Preço Atual (R$)", value=10.0)

        if st.button("🚀 EXECUTAR ANÁLISE"):
            vi = math.sqrt(22.5 * lpa_v * vpa_v) if lpa_v > 0 else 0
            st.success(f"**Valor Intrínseco (Graham Cap 6.5): R$ {vi:.2f}**")
            if roe_v < s_ui: st.error(f"🚨 AVA-1: ROE {roe_v}% abaixo da Selic (Ke).")

# --- MÓDULO C: VISÃO DO BOSQUE ---
with aba_c:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.3 - ALOCAÇÃO</span>', unsafe_allow_html=True)
    txt_bosque = st.text_area("COLE A LISTA DE ATIVOS DO INVESTIDOR10:")
    apt = st.number_input("Aporte Mensal R$:", value=1000.0)
    
    if st.button("⚖️ ANALISAR CARTEIRA"):
        tks = re.findall(r"([A-Z]{4}\d{1,2})", txt_bosque.upper())
        if tks:
            st.success(f"✅ {len(tks)} ativos identificados.")
            df_b = pd.DataFrame({"Ticker": list(dict.fromkeys(tks))})
            st.table(df_b)
            # Grande Virada (C.3)
            pv = (apt * 12) / 0.08
            st.info(f"🌱 Ponto da Grande Virada (Cap 8.5.1): R$ {pv:,.2f} (est.)")

# --- MÓDULO CHAT: O MESTRE DIGITAL ---
with aba_chat:
    st.subheader("💬 Fale com o Mestre Digital")
    if CHAT_OK:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Olá, cultivador. Sou o Mestre Digital do livro R.E.N.D.A. Como posso ajudar?"}]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Pergunte ao Mestre..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                resp = chat_model.generate_content(f"Aja como o Mestre Digital do livro Método R.E.N.D.A. Pergunta: {prompt}").text
                st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})
    else:
        st.error("Configure a API Key para o Chat funcionar.")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL™ V.102.09 SUPREME © 2026 Laerson Endrigo Ely")
