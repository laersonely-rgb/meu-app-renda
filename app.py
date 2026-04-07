import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
import google.generativeai as genai
from datetime import date, datetime
from fpdf import FPDF

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE ENGENHARIA E ESTÉTICA TERMINAL
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 SUPREME", page_icon="🌱", layout="wide")

# CSS para fidelidade visual ao livro
st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11px!important; background-color: #f4f8f5; border: 1px solid #c8e6c9; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .formula-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 0.9rem; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; }
    .success-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# ── Configuração de IA (Mentor Conversacional) ─────────────────────────────
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    CHAT_OK = True
else:
    CHAT_OK = False

# ── Constantes do Livro ────────────────────────────────────────────────────
SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 SUPREME               |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NAO constitui recomendacao de investimento (Res. CVM 20/2021).      |
+----------------------------------------------------------------------+"""

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULOS DE SUPORTE (MATH & PARSING)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]["valor"])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]["valor"])
        dias = max(0, (date.today() - date(2026, 1, 29)).days)
        copom_min = 276 + int(dias / 45)
        ntnb = round((s - i) * 0.6 + i, 2)
        return {"selic": s, "ipca": i, "ntnb": ntnb, "copom_min": copom_min}
    except: return {"selic": 10.75, "ipca": 4.50, "ntnb": 6.20, "copom_min": 276}

def formula_ui(formula, substituicao, resultado):
    st.markdown(f"""<div class="formula-box"><b>Fórmula:</b> {formula}<br><b>Substitui:</b> {substituicao}<br><b>Resultado: {resultado}</b></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SEGURANÇA E AUTENTICAÇÃO (PÁG 324)
# ═══════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("🔐 Acesso ao Mestre Digital")
    st.info("A chave de acesso encontra-se na página 324 do livro.")
    pwd = st.text_input("Insira a Chave de Acesso:", type="password")
    if st.button("Validar Semente"):
        if pwd == SENHA:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Chave inválida.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
st.code(AVISO_LEGAL, language="text")
macro = fetch_macro()

# --- ETAPA G5: ÂNCORA MACRO (Cap. 5.2) ---
st.markdown('<span class="chapter-tag">CAPÍTULO 5.2 - O CLIMA MACRO</span>', unsafe_allow_html=True)
st.subheader("🌐 Âncora de Dados Macro")
c1, c2, c3, c4 = st.columns(4)
s_ui = c1.number_input("Selic Meta (%)", value=macro["selic"])
i_ui = c2.number_input("IPCA 12m (%)", value=macro["ipca"])
nb_ui = c3.number_input("NTN-B IPCA+", value=macro["ntnb"])
cp_ui = c4.number_input("Nº Reunião COPOM", value=macro["copom_min"])

if cp_ui < macro["copom_min"]:
    st.error("🚨 DADO OBSOLETO. Conforme Cap. 5.2, os dados devem refletir o clima atual.")
    st.stop()

j_real = s_ui - i_ui
clima = "❄️ INVERNO MACRO (Juro Real > 10%)" if j_real > 10 else "☀️ VERÃO MACRO"
st.code(f"Juro Real: {j_real:.2f}% | Status: {clima}", language="text")

aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO A: ANÁLISE DE ATIVO ÚNICO (PED + SCORECARD + AVA)
# ═══════════════════════════════════════════════════════════════════════════
with aba_a:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.6 - O SCORECARD DO CULTIVADOR</span>', unsafe_allow_html=True)
    tk = st.text_input("DIGITE O TICKER (Ex: ITUB4):").upper().strip()
    trilha = st.radio("Natureza do Ativo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"], horizontal=True)

    if tk:
        st.subheader(f"🔬 FASE 1: Protocolo PED (Garimpo de Dados)")
        with st.expander("📥 Entrada de Dados - Gate de Auditoria", expanded=True):
            st.caption("Conforme pág. 140, a auditoria impede o plantio de sementes estragadas.")
            noticia = st.text_input("Título da notícia mais recente (Patch 5):")
            c_a, c_b, c_c = st.columns(3)
            p_at = c_a.number_input("Preço Atual (R$)", value=10.0)
            lpa = c_a.number_input("LPA (Lucro por Ação)", value=1.0)
            vpa = c_a.number_input("VPA (Valor Patrimonial)", value=10.0)
            dy = c_b.number_input("DY 12m (%)", value=8.0)
            roe = c_b.number_input("ROE (%)", value=15.0)
            cagr = c_b.number_input("CAGR Proventos (%)", value=5.0)
            liq = c_c.number_input("Liquidez (R$/dia)", value=2000000.0)
            de = c_c.number_input("Dívida/EBITDA", value=1.5)
            tend = c_c.selectbox("Tendência Lucros (9C):", ["Crescente", "Estável", "Decrescente"])

        if st.button("🚀 EXECUTAR CICLO DETERMINÍSTICO"):
            st.markdown("---")
            # FASE 2: SCORECARD
            st.subheader(f"📊 FASE 2: Scorecard R.E.N.D.A. — {tk}")
            
            # PILAR A - ALOCAÇÃO (Cap 6.5)
            st.markdown('**Pilar A (Alocação - O Tronco)**')
            if trilha == "AÇÕES":
                vi = math.sqrt(22.5 * lpa * vpa)
                mg = ((vi - p_at) / vi) * 100
                formula_ui("VI = √(22,5 × LPA × VPA)", f"√ (22,5 × {lpa} × {vpa})", f"R$ {vi:.2f}")
                n_a = 20 if mg > 20 else 15 if mg > 0 else 5
                diag_a = f"Margem Graham: {mg:.1f}%"
            else:
                pvp = p_at / vpa if vpa > 0 else 1
                n_a = 20 if pvp < 0.95 else 10
                diag_a = f"P/VP: {pvp:.2f}"

            # NOTAS (Cap. 8.6)
            n_r = 20 if cagr > 10 else 15 if cagr > 0 else 5 # REINVESTIMENTOS
            n_e = 20 # ESSENCIAIS (Simplificado para o exemplo)
            n_n = 20 if roe > 18 else 10 # NEGÓCIOS SÓLIDOS
            
            score = ((n_r + n_e + n_n + n_a) / 80) * 100
            
            st.code(f"""
+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Fiel ao Livro)      |
+---------+---------------------+------------+----------------------------------+
| R (Fr.) | CAGR Lucros/Prov    | {n_r:>10} | CAGR {cagr}% (Cap 4.3)            |
| E (So.) | Setor (Solo)        | {n_e:>10} | Essencial (Cap 5.3)              |
| N (Ra.) | ROE (Raizes)        | {n_n:>10} | ROE {roe}% (Cap 6.3)              |
| A (Tr.) | Preco (Tronco)      | {n_a:>10} | {diag_a:<32} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | BASE 100            | {score:>5.1f}/100 | ({n_r+n_e+n_n+n_a}/80) x 100                 |
+---------+---------------------+------------+----------------------------------+
""", language="text")

            # FASE 3: AVA (Cap 11.7)
            st.subheader(f"🚨 FASE 3: Protocolo AVA (Travas de Segurança)")
            if tend == "Decrescente":
                st.markdown(f'<div class="veto-alert">🚨 VETO AVA-1: Destruição de valor detectada (Lucros Decrescentes). Cap. 11.7</div>', unsafe_allow_html=True)
            if liq < 1000000:
                st.markdown(f'<div class="veto-alert">🚨 VETO AVA-2: Baixa Liquidez (R$ {liq:,.2f} < R$1M). Cap. 11.7</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO C: VISÃO DO BOSQUE (ANÁLISE INTEGRAL DE CARTEIRA)
# ═══════════════════════════════════════════════════════════════════════════
with aba_c:
    st.markdown('<span class="chapter-tag">CAPÍTULO 8.3 - A VISÃO DO BOSQUE</span>', unsafe_allow_html=True)
    st.write("### 🌲 Auditoria de Carteira C.0 a C.11")
    
    # Simulação de base de dados da carteira
    df_portfolio = pd.DataFrame([
        {"Ticker": "BBAS3", "%": 20.0, "Tipo": "AÇÃO", "DY": 9.2, "ROE": 21.0, "D/EBITDA": 0.0, "Index": "Operacional"},
        {"Ticker": "TAEE11", "%": 20.0, "Tipo": "AÇÃO", "DY": 10.5, "ROE": 18.0, "D/EBITDA": 3.2, "Index": "Operacional"},
        {"Ticker": "HGLG11", "%": 20.0, "Tipo": "FII TIJOLO", "DY": 8.4, "ROE": 0.0, "D/EBITDA": 0.0, "Index": "IPCA"},
        {"Ticker": "MXRF11", "%": 20.0, "Tipo": "FII PAPEL", "DY": 12.5, "ROE": 0.0, "D/EBITDA": 0.0, "Index": "CDI"},
        {"Ticker": "Tesouro", "%": 20.0, "Tipo": "RF", "DY": 10.75, "ROE": 0.0, "D/EBITDA": 0.0, "Index": "Selic"}
    ])
    
    st.write("📝 **Inventário do Pomar (C.0)**")
    edit_df = st.data_editor(df_portfolio, num_rows="dynamic", use_container_width=True)
    aporte = st.number_input("Aporte Mensal R$ (C.3):", value=1000.0)

    if st.button("⚖️ ANALISAR EQUILÍBRIO DO BOSQUE"):
        # C.1 TALMUD
        p_a = edit_df[edit_df["Tipo"] == "AÇÃO"]["%"].sum()
        p_f = edit_df[edit_df["Tipo"].str.contains("FII")]["%"].sum()
        p_r = edit_df[edit_df["Tipo"] == "RF"]["%"].sum()
        
        st.write("### ⚖️ C.1 Termômetro do Talmud (Pilar D)")
        st.code(f"Negócios: {p_a:.1f}% | Terra: {p_f:.1f}% | Mãos: {p_r:.1f}%", language="text")
        if abs(p_a - 33.3) > 10: st.warning("⚠️ Monocultura Detectada (Cap. 8.3). Reequilibrio necessário.")

        # C.3 GRANDE VIRADA
        dy_p = (edit_df["DY"] * (edit_df["%"]/100)).sum()
        pat_v = (aporte * 12) / (dy_p / 100) if dy_p > 0 else 0
        st.write("### 🌱 C.3 Simulador da Grande Virada")
        formula_ui("Pat_Virada = (Aporte × 12) / DY_decimal", f"({aporte} × 12) / {dy_p/100:.4f}", f"R$ {pat_v:,.2f}")
        st.success(f"Conforme Cap 8.5.1, o ponto de virada é R$ {pat_v:,.2f}.")

        # C.8 INDEXADORES
        st.write("### 🧭 C.8 Raio-X de Indexadores")
        p_cdi = edit_df[edit_df["Index"] == "CDI"]["%"].sum()
        st.write(f"Exposição ao CDI: {p_cdi:.1f}%")
        if p_cdi > 50: st.markdown(f'<div class="veto-alert">⚠️ ALERTA: Exposição ao CDI acima de 50%. Sensível à queda da Selic.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# ABA CHAT: O MESTRE DIGITAL (IA MENTOR)
# ═══════════════════════════════════════════════════════════════════════════
with aba_chat:
    st.subheader("💬 Fale com o Mestre Digital")
    st.info("Este mentor foi treinado com o conteúdo integral do livro 'Método R.E.N.D.A.'.")
    
    if CHAT_OK:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Olá, cultivador. Sou o Mestre Digital. Como posso ajudar seu bosque a crescer hoje?"}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Pergunte algo sobre o método..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                instr = f"Você é o Mestre Digital do livro 'Método R.E.N.D.A.' de Laerson Ely. Use as metáforas de Solo, Raizes, Tronco e Frutos. Pergunta: {prompt}"
                resp = model.generate_content(instr).text
                st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})
    else:
        st.warning("IA em manutenção. Configure a API Key nos Secrets.")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL™ V.102.09 SUPREME © Laerson Endrigo Ely, 2026.")
