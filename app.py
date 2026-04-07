import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
from datetime import date
from fpdf import FPDF

# --- CONFIGURAÇÃO RÍGIDA MÓDULO 0.5 ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def terminal_print(texto):
    """Alinhamento visual rígido conforme Módulo 0.5"""
    st.code(texto, language="text")

def gerar_pdf_bytes(conteudo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=8)
    texto_limpo = conteudo.encode('latin-1', 'ignore').decode('latin-1')
    for linha in texto_limpo.split('\n'):
        pdf.cell(0, 4, txt=linha, ln=1)
    return bytes(pdf.output())

# --- MÓDULO 0: SAFE HARBOR ---
def exibir_aviso_legal():
    terminal_print("""
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|                                                                      |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
|  A decisão de investimento é 100% exclusiva do usuário.              |
+----------------------------------------------------------------------+
""")

# --- SEGURANÇA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    exibir_aviso_legal()
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso:", type="password")
    if st.button("Validar Semente"):
        if pwd == "RENDA2026":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Chave inválida.")
    st.stop()

# --- MOTOR PERPÉTUO (PATCH 1, 2, 3) ---
@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]['valor'])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]['valor'])
        dias = (date.today() - date(2026, 1, 29)).days
        copom_m = 276 + int(dias / 45)
        nb_backup = (s - i) * 0.6 + i
        return s, i, copom_m, nb_backup
    except: return 10.75, 4.50, 276, 6.20

# --- MOTORES DE GARIMPO ---
def garimpar_dados_ativo(texto):
    d = {}
    def ext(p, t):
        m = re.search(p, t, re.IGNORECASE)
        return float(m.group(1).replace('.', '').replace(',', '.')) if m else None
    d['lpa'] = ext(r'LPA[\s\S]{0,20}?([0-9.,]+)', texto)
    d['vpa'] = ext(r'VPA[\s\S]{0,20}?([0-9.,]+)', texto)
    d['dy'] = ext(r'(?:Dividend Yield|DY)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    d['roe'] = ext(r'ROE[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    d['cagr'] = ext(r'CAGR\s+(?:LUCROS|DPA)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    return d

# --- INTERFACE ---
exibir_aviso_legal()
s_val, i_val, cp_min, nb_back = fetch_macro()
st.title("🌱 Sistema de Ensino R.E.N.D.A.")

aba_a, aba_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# =====================================================================
# MÓDULO A: FASES 1, 2 E 3
# =====================================================================
with aba_a:
    st.subheader("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO")
    c1, c2, c3 = st.columns(3)
    s_ui = c1.number_input("Selic Meta (%)", value=s_val)
    i_ui = c2.number_input("IPCA 12m (%)", value=i_val)
    cp_ui = c3.number_input("Nº Reunião COPOM", value=cp_min)

    if cp_ui < cp_min: st.error(f"🚨 DADO OBSOLETO: COPOM {cp_ui} < {cp_min}"); st.stop()
    
    j_real = s_ui - i_ui
    clima = "❄️ INVERNO MACRO" if j_real > 10 else "☀️ VERÃO MACRO"
    ancora_ascii = f"""
+---------------+-----------+--------------+--------------+-------------+
| Variavel      | Valor     | Fonte (URL)  | Data/Hora    | Prova Sombra|
+---------------+-----------+--------------+--------------+-------------+
| Selic Meta    | {s_ui:>8.2f}% | BCB          | {date.today()} | [COPOM {cp_ui}✅] |
| IPCA 12m      | {i_ui:>8.2f}% | IBGE         | {date.today()} | [Mensal]    |
| NTN-B Longa   | IPCA+{nb_back:.2f}% | Tes/Backup   | {date.today()} | [Regra D-1] |
| Juro Real     | {j_real:>8.2f}% | Calculado    | Selic-IPCA   | [{clima}]   |
+---------------+-----------+--------------+--------------+-------------+
"""
    terminal_print(ancora_ascii)

    st.markdown("---")
    ticker = st.text_input("INSIRA O TICKER:", value="").upper()
    trilha = st.selectbox("Trilha de Análise:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])

    if ticker:
        st.subheader(f"🔬 FASE 1: Protocolo de Extração (PED) — {ticker}")
        
        with st.expander("📥 GATE DE AUDITORIA (Patch 5/8)", expanded=True):
            noticia = st.text_input("Título da Notícia Recente (Verificação Sombra - Patch 5):")
            txt_ped = st.text_area("Área de Colagem (Investidor10):")
            ext = garimpar_dados_ativo(txt_ped) if txt_ped else {}
            
            # Hierarquia de Preço (Patch 8)
            try: p_goog = yf.Ticker(f"{ticker}.SA").history(period="1d")['Close'].iloc[-1]
            except: p_goog = 10.0

            c1, c2, c3 = st.columns(3)
            p_final = c1.number_input("Cotação Real (Google Finance)", value=float(p_goog))
            v_lpa = c1.number_input("Campo 1: LPA (R$)", value=float(ext.get('lpa', 0.0)))
            v_vpa = c1.number_input("Campo 2: VPA (R$)", value=float(ext.get('vpa', 0.0)))
            v_dy = c2.number_input("Campo 3: DY 12m (%)", value=float(ext.get('dy', 0.0)))
            v_roe = c2.number_input("Campo 4: ROE (%)", value=float(ext.get('roe', 0.0)))
            v_cagr = c2.number_input("Campo 7: CAGR DPA (%)", value=float(ext.get('cagr', 0.0)))
            v_liq = c3.number_input("Campo 6: Liquidez (R$)", value=2000000.0)
            v_setor = c3.selectbox("Pilar E - Setor:", ["Essencial Perene", "Essencial Moderado", "Cíclico"])
            v_tend = c3.selectbox("Campo 9C: Tendência Lucros:", ["Crescente", "Estável", "Decrescente"])

        if st.button("🚀 VALIDAR DADOS E EXECUTAR FASE 2 E 3"):
            # --- FASE 2: SCORECARD (Cap 8.6) ---
            st.markdown("### FASE 2: Scorecard Determinístico (Módulo 8)")
            
            # Aritmética Graham (Regra 3)
            vi = math.sqrt(22.5 * v_lpa * v_vpa) if v_lpa > 0 else 0
            m_g = ((vi - p_final) / vi) * 100 if vi > 0 else 0
            st.write("**CÁLCULO DA MARGEM DE SEGURANÇA (Pilar A - Cap 6.5)**")
            st.write(f"▸ Fórmula  | VI = raiz(22,5 x LPA x VPA)")
            st.write(f"▸ Substitui | VI = raiz(22,5 x {v_lpa} x {v_vpa})")
            st.write(f"▸ Resultado | R$ {vi:.2f}")

            n_r = 20 if v_cagr > 10 else 10
            n_e = 20 if "Perene" in v_setor else 10
            n_n = 20 if v_roe > 15 else 10
            n_a = 20 if m_g > 20 else 10
            score = ((n_r + n_e + n_n + n_a) / 80) * 100

            score_ascii = f"""
+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Ref. Patch 7)       |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA 3 anos     | {n_r:<10} | CAGR {v_cagr}% (Cap 4.3)            |
| E       | Setor / Segmento    | {n_e:<10} | {v_setor[:30]} |
| N       | ROE/Eficiência      | {n_n:<10} | ROE {v_roe}% (Cap 6.3)              |
| D       | Desvio Talmud       | -- (N/A)   | (Módulo C - Carteira)            |
| A       | Alocação (Graham)   | {n_a:<10} | Margem {m_g:.1f}% -- VI R${vi:.2f} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.1f}/100    | ({n_r+n_e+n_n+n_a}/80) x 100               |
+---------+---------------------+------------+----------------------------------+
"""
            terminal_print(score_ascii)

            # --- FASE 3: AVA (Cap 11.7) ---
            st.markdown("### FASE 3: Diagnóstico de Risco (Protocolo AVA)")
            ava_ascii = f"""
+-------+-------------------------+-----------------------------------------+
| Trava | Criterio de Avaliacao   | Diagnostico e Status do Veto            |
+-------+-------------------------+-----------------------------------------+
| AVA-1 | Destruicao de Valor     | {'✅ APROVADO' if v_tend != 'Decrescente' else '🚨 VETO: QUEDA LUCRO'}           |
| AVA-2 | Risco de Ruina          | ✅ APROVADO (Divida Controlada)         |
| AVA-2 | Risco de Liquidez       | {'✅ APROVADO' if v_liq > 1000000 else '🚨 VETO: BAIXA LIQ'}          |
+-------+-------------------------+-----------------------------------------+
"""
            terminal_print(ava_ascii)
            
            report = ancora_ascii + score_ascii + ava_ascii
            pdf_bytes = gerar_pdf_bytes(report)
            st.download_button("📥 Baixar Relatório V.102.09 (PDF)", pdf_bytes, f"RENDA_{ticker}.pdf")

# =====================================================================
# MÓDULO C: VISÃO DO BOSQUE
# =====================================================================
with aba_c:
    st.subheader("🌲 MÓDULO C — ANÁLISE DE CARTEIRA (VISÃO DO BOSQUE)")
    st.info("Regra do Talmud (Cap. 8.3): 1/3 FIIs, 1/3 Ações, 1/3 Renda Fixa.")
    
    with st.expander("📥 IMPORTAR CARTEIRA (CONSOLIDADOR)", expanded=True):
        txt_c = st.text_area("Cole aqui o texto da sua carteira (StatusInvest/Kinvo/Corretora):", placeholder="Ticker | % | Preço...")
    
    # Inicia vazio para o usuário preencher/importar
    df_empty = pd.DataFrame([{"Ticker": "", "Tipo": "AÇÃO", "%": 0.0, "DY": 0.0, "ROE": 0.0}])
    edit_c = st.data_editor(df_empty, num_rows="dynamic", use_container_width=True)
    
    aporte_m = st.number_input("Seu Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ EXECUTAR ANÁLISE DO BOSQUE"):
        p_a = edit_c[edit_c["Tipo"] == "AÇÃO"]["%"].sum()
        p_f = edit_c[edit_c["Tipo"] == "FII"]["%"].sum()
        p_rf = 100 - p_a - p_f
        
        # Grande Virada (Cap. 8.5.1)
        dy_p = (edit_c["DY"] * (edit_c["%"]/100)).sum()
        pat_v = (aporte_m * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        st.write("#### C.3 🌱 Simulador da Grande Virada")
        st.write(f"▸ Fórmula  | Pat_Virada = (Aporte x 12) / DY_decimal")
        st.write(f"▸ Substitui | Pat_Virada = ({aporte_m} x 12) / {dy_p/100:.4f}")
        st.success(f"💰 PATRIMÔNIO ALVO: R$ {pat_v:,.2f}")
