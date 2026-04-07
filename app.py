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
    ntnb = round((s - i)
