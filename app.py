import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
from datetime import date, datetime
from fpdf import FPDF

# ═══════════════════════════════════════════════════════════════════════════
# ARQUITETURA DE ELITE - ENGENHARIA R.E.N.D.A.
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.stCodeBlock pre{font-size:11px!important; background-color: #f4f8f5;}
.chapter-tag{background: #1b5e20; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold;}
.formula-box{background:#e8f5e9; border-left:5px solid #2e7d32; padding:15px; margin:10px 0; font-family: 'Courier New', monospace;}
.veto-box{background:#ffebee; border-left:5px solid #c62828; padding:10px; margin:5px 0;}
</style>""", unsafe_allow_html=True)

# ── Globais ───────────────────────────────────────────────────────────────
SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 FULL                  |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
+----------------------------------------------------------------------+"""

# ── Segurança ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso (pág. 324):", type="password")
    if st.button("Validar Semente"):
        if pwd == SENHA:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Chave inválida.")
    st.stop()

# ── Motor Macro ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]["valor"])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]["valor"])
        dias = max(0, (date.today() - date(2026, 1, 29)).days)
        copom_min = 276 + int(dias / 45)
        return s, i, copom_min
    except: return 10.75, 4.50, 276

s_val, i_val, cp_min = fetch_macro()

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE
# ═══════════════════════════════════════════════════════════════════════════
st.code(AVISO_LEGAL, language="text")
st.title("🌱 Sistema de Ensino R.E.N.D.A. <small>v102.09</small>", unsafe_allow_html=True)

# G5 - ÂNCORA MACRO
st.markdown('<span class="chapter-tag">CAP. 5.2 - O CLIMA MACRO</span>', unsafe_allow_html=True)
cm1, cm2, cm3 = st.columns(3)
s_ui = cm1.number_input("Selic (%)", value=s_val)
i_ui = cm2.number_input("IPCA 12m (%)", value=i_val)
cp_ui = cm3.number_input("Nº Reunião COPOM", value=int(cp_min))

if cp_ui < cp_min:
    st.error("🚨 DADO OBSOLETO. Verifique a reunião do COPOM.")
    st.stop()

aba_a, aba_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO C — VISÃO DO BOSQUE (ANÁLISE INTEGRAL)
# ═══════════════════════════════════════════════════════════════════════════
with aba_c:
    st.markdown('<span class="chapter-tag">CAP. 8.3 - A MATRIZ DE ALOCAÇÃO</span>', unsafe_allow_html=True)
    st.info("A análise de carteira avalia o equilíbrio milenar do Talmud: Negócios (Ações), Terra (FIIs) e Mãos (RF).")

    # Editor de Dados da Carteira
    st.write("### 📝 Inventário do Pomar")
    df_empty = pd.DataFrame([
        {"Ticker": "BBAS3", "%": 25.0, "Tipo": "AÇÃO", "Setor": "Bancos", "DY": 9.0, "ROE": 21.0, "D/EBITDA": 0.0, "CAGR DPA": 8.0, "Liq": 200.0, "Tend": "Crescente"},
        {"Ticker": "HGLG11", "%": 25.0, "Tipo": "FII TIJOLO", "Setor": "Logística", "DY": 8.5, "ROE": 0.0, "LTV": 12.0, "CAGR DPA": 4.0, "Liq": 10.0, "Tend": "Estável"},
        {"Ticker": "MXRF11", "%": 25.0, "Tipo": "FII PAPEL", "Setor": "Papel CRI", "DY": 12.0, "ROE": 0.0, "LTV": 0.0, "CAGR DPA": 2.0, "Liq": 15.0, "Tend": "Estável"},
        {"Ticker": "Tesouro", "%": 25.0, "Tipo": "RF", "Setor": "Reserva", "DY": 10.75, "ROE": 0.0, "LTV": 0.0, "CAGR DPA": 0.0, "Liq": 1000.0, "Tend": "Estável"}
    ])
    
    edit_df = st.data_editor(df_empty, num_rows="dynamic", use_container_width=True)
    
    col_ap1, col_ap2 = st.columns(2)
    patrimonio = col_ap1.number_input("Patrimônio Total Atual (R$):", value=10000.0)
    aporte_m = col_ap2.number_input("Próximo Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ EXECUTAR PROTOCOLO VISÃO DO BOSQUE"):
        st.markdown("---")
        
        # C.0 - MAPEAMENTO
        st.write("### C.0 - Mapeamento Genético")
        # Lógica de Classificação
        edit_df['Natureza'] = edit_df.apply(lambda r: "Papel" if "PAPEL" in r['Tipo'] else ("Tijolo" if "TIJOLO" in r['Tipo'] else "Negócios"), axis=1)
        st.table(edit_df[['Ticker', '%', 'Tipo', 'Setor', 'Natureza']])

        # C.1 - TALMUD (Pilar D)
        st.write("### C.1 - Termômetro do Talmud (Pilar D)")
        p_a = edit_df[edit_df["Tipo"] == "AÇÃO"]["%"].sum()
        p_f = edit_df[edit_df["Tipo"].str.contains("FII")]["%"].sum()
        p_rf = edit_df[edit_df["Tipo"] == "RF"]["%"].sum()
        dev = (abs(p_a - 33.3) + abs(p_f - 33.3) + abs(p_rf - 33.4)) / 3
        
        st.code(f"""
+------------------+-------+--------+----------+-----------------------------------+
| Classe           | Atual | Alvo   | Desvio   | Status (Ref. Cap 8.3)             |
+------------------+-------+--------+----------+-----------------------------------+
| Negocios (Acoes) | {p_a:>4.1f}% | 33.33% | {p_a-33.3:>+5.1f}pp | {'✅ OK' if abs(p_a-33.3)<5 else '⚠️ DESVIO'}                |
| Terra (FIIs)     | {p_f:>4.1f}% | 33.33% | {p_f-33.3:>+5.1f}pp | {'✅ OK' if abs(p_f-33.3)<5 else '⚠️ DESVIO'}                |
| Maos (RF/Res)    | {p_rf:>4.1f}% | 33.33% | {p_rf-33.4:>+5.1f}pp | {'✅ OK' if abs(p_rf-33.4)<5 else '⚠️ DESVIO'}               |
+------------------+-------+--------+----------+-----------------------------------+
""", language="text")

        # C.3 - GRANDE VIRADA
        st.write("### 🌱 C.3 - Simulador da Grande Virada")
        st.markdown('<span class="chapter-tag">CAP. 8.5.1 - QUANDO A RENDA SUPERA O APORTE</span>', unsafe_allow_html=True)
        dy_p = (edit_df["DY"] * (edit_df["%"]/100)).sum()
        pat_v = (aporte_m * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        st.markdown(f"""<div class="formula-box">
        <b>Fórmula | Pat_Virada = (Aporte × 12) / DY_decimal</b><br>
        Substitui | (R$ {aporte_m:,.2f} × 12) / {dy_p/100:.4f}<br>
        Resultado | <b>Patrimônio Alvo: R$ {pat_v:,.2f}</b>
        </div>""", unsafe_allow_html=True)

        # C.4 e C.10 - TESTE ÁCIDO E YIELD TRAP
        st.write("### 🔬 Análise de Vitalidade (C.4 e C.10)")
        
        for _, row in edit_df.iterrows():
            # C.4 Teste Ácido
            if row['Tipo'] == "AÇÃO":
                spread = row['ROE'] - s_ui
                if spread < 0:
                    st.markdown(f'<div class="veto-box">🚨 <b>{row["Ticker"]}</b>: Destruição de Valor (ROE {row["ROE"]}% < Selic {s_ui}%).</div>', unsafe_allow_html=True)
            
            # C.10 Yield Trap
            if row['DY'] > (row['CAGR DPA'] * 1.5) and row['DY'] > 12:
                st.markdown(f'<div class="veto-box">⚠️ <b>{row["Ticker"]}</b>: Possível Yield Trap (DY {row["DY"]}% muito acima do CAGR {row["CAGR DPA"]}%).</div>', unsafe_allow_html=True)

        # C.11 - ALAVANCAGEM FII
        fiis_tijolo = edit_df[edit_df["Tipo"] == "FII TIJOLO"]
        if not fiis_tijolo.empty:
            st.write("### 🏗️ C.11 - Termômetro de Alavancagem FII")
            for _, row in fiis_tijolo.iterrows():
                status_ltv = "✅ SEGURO" if row['LTV'] < 15 else "🚨 CRÍTICO"
                st.write(f"**{row['Ticker']}**: LTV {row['LTV']}% - Status: {status_ltv}")

        # REEQUILÍBRIO DE APORTE
        st.write("### 🎯 Sugestão de Alocação de Aporte")
        classes = {"AÇÃO": p_a, "FII": p_f, "RF": p_rf}
        min_class = min(classes, key=classes.get)
        st.success(f"Para equilibrar o Talmud, seu próximo aporte de **R$ {aporte_m:,.2f}** deve focar em: **{min_class}**.")

# MÓDULO A (Preservado da versão anterior)
with aba_a:
    st.info("Insira um Ticker para realizar a auditoria individual de 3 Fases (PED, Scorecard e AVA).")
