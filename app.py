import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
import google.generativeai as genai
from datetime import date, datetime

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÃO DE ELITE E ESTÉTICA
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 SUPREME", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11.5px!important; background-color: #f4f8f5; border: 1px solid #c8e6c9; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; margin: 5px 0;}
    .ok-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; color: #1b5e20; margin: 5px 0;}
    .warn-box { background: #fff3e0; border-left: 5px solid #e65100; padding: 10px; border-radius: 4px; color: #e65100; margin: 5px 0;}
</style>
""", unsafe_allow_html=True)

SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 SUPREME               |
|                                                                      |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NAO constitui recomendacao de investimento (Res. CVM 20/2021).      |
|  A decisao de investimento e 100% exclusiva do usuario.              |
+----------------------------------------------------------------------+"""

RODAPE = """\
----------------------------------------------------------------------------
  R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL (Portfolio Edition)
  (c) Laerson Endrigo Ely, 2026. Todos os direitos reservados.
----------------------------------------------------------------------------"""

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ═══════════════════════════════════════════════════════════════════════════
# 2. MOTORES DE BUSCA (MACRO, PREÇO E GARIMPO)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_macro():
    now = datetime.now().strftime("%d/%m %H:%M")
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()[0]["valor"])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()[0]["valor"])
        src = "BCB API"
    except:
        s, i, src = 10.75, 4.50, "FALLBACK"
    
    dias = max(0, (date.today() - date(2026, 1, 29)).days)
    copom_min = 276 + int(dias / 45)
    ntnb = round((s - i) * 0.6 + i, 2)
    return {"selic": s, "ipca": i, "ntnb": ntnb, "copom_min": copom_min, "now": now, "src": src}

def fetch_cotacao(ticker):
    if not ticker: return 0.0
    try:
        t = ticker.upper().strip()
        tk_obj = yf.Ticker(f"{t}.SA")
        preco = tk_obj.fast_info['lastPrice']
        if preco > 0: return round(preco, 2)
        return round(yf.Ticker(t).fast_info['lastPrice'], 2)
    except: return 0.0

def parse_liquidez(raw):
    if not raw: return 0.0
    s = str(raw).strip().upper()
    mul = 1
    if "BILH" in s: mul = 1_000_000_000
    elif "MILH" in s: mul = 1_000_000
    elif "K" in s: mul = 1_000
    num = re.sub(r"[^\d,\.]", "", s).replace(".", "").replace(",", ".")
    try:
        v = float(num)
        return v * mul if v < 1000000 else v
    except: return 0.0

def garimpar_ped(texto):
    t = texto.upper()
    def _find(p):
        m = re.search(p, t)
        if m:
            val = m.group(1).replace(".", "").replace(",", ".")
            try: return float(val)
            except: return 0.0
        return 0.0
    m_liq = re.search(r"LIQUIDEZ[\s\S]{0,80}?(R?\$?\s*[\d]+[,.][\d]+(?:MILH|BILH|K|M|B)?)", t)
    return {
        "lpa": _find(r"LPA[\s\S]{0,50}?([-]?\d+[,.]\d+)"),
        "vpa": _find(r"VPA[\s\S]{0,50}?(\d+[,.]\d+)"),
        "dy": _find(r"(?:YIELD|DY)[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "roe": _find(r"ROE[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "de": _find(r"D[IÍ]V[\s\S]{0,15}?EBITDA[\s\S]{0,30}?(\d+[,.]\d+)"),
        "cagr": _find(r"CAGR[\s\S]{0,30}?(?:DPA|DIVIDENDO)[\s\S]{0,20}?(\d+[,.]\d+)\s*%"),
        "vac": _find(r"VAC[AÂ]NCIA[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "iad": _find(r"INADIMPL[EÊ]NCIA[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "ltv": _find(r"LTV[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "liq_raw": m_liq.group(1) if m_liq else ""
    }

# ═══════════════════════════════════════════════════════════════════════════
# 3. LÓGICA DO SCORECARD (REGRAS RÍGIDAS DO LIVRO)
# ═══════════════════════════════════════════════════════════════════════════
def pilar_R(cagr):
    if cagr > 10: return 20, f"CAGR {cagr:.1f}% Frutos Acelerados"
    if cagr > 5: return 15, f"CAGR {cagr:.1f}% Frutos Crescentes"
    if cagr > 0: return 10, f"CAGR {cagr:.1f}% Frutos Estaveis"
    return 5, f"CAGR {cagr:.1f}% Estagnado"

def pilar_E(setor, tipo):
    s = str(setor).lower()
    if "fii" in tipo.lower():
        if any(x in s for x in ["logist","
