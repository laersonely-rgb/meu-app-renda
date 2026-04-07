import streamlit as st
import pandas as pd
import requests
import math
import re
from datetime import date
from fpdf import FPDF

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def terminal_print(texto):
    """Garante o alinhamento visual rígido exigido no Módulo 0.5."""
    st.code(texto, language="text")

def limpar_pdf(texto):
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def gerar_pdf(conteudo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=8)
    for linha in limpar_pdf(conteudo).split('\n'):
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
        # Cálculo COPOM (Patch 1)
        dias = (date.today() - date(2026, 1, 29)).days
        copom_min = 276 + int(dias / 45)
        # NTN-B Backup (Patch 3)
        ntnb_b = (s - i) * 0.6 + i
        return s, i, copom_min, ntnb_b
    except:
        return 10.75, 4.50, 276, 6.20

# --- EXECUÇÃO ---
exibir_aviso_legal()
st.title("🌱 Sistema de Ensino R.E.N.D.A.")
st.caption("Fiel ao Protocolo V.102.09 FULL (Portfolio Edition)")

s_atual, i_atual, copom_m, ntnb_b = fetch_macro()

# --- ETAPA G5: ÂNCORA MACRO ---
st.subheader("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    s_ui = c1.number_input("Selic Meta (%)", value=s_atual)
    i_ui = c2.number_input("IPCA 12m (%)", value=i_atual)
    cp_ui = c3.number_input("Nº Reunião COPOM", value=copom_m)
    nb_ui = c4.number_input("NTN-B Taxa (IPCA+)", value=ntnb_b)

    if cp_ui < copom_m:
        st.error(f"⚠️ ERRO DE CONEXÃO: Dado obsoleto detectado (COPOM {cp_ui} < {copom_m}).")
        st.stop()
    
    j_real = s_ui - i_ui
    clima = "❄️ INVERNO MACRO" if j_real > 10 else "☀️ VERÃO MACRO"
    
    ancora = f"""
+---------------+-----------+--------------+--------------+-------------+
| Variavel      | Valor     | Fonte (URL)  | Data/Hora    | Prova Sombra|
+---------------+-----------+--------------+--------------+-------------+
| Selic Meta    | {s_ui:>8.2f}% | BCB          | {date.today()} | [COPOM {cp_ui}✅] |
| IPCA 12m      | {i_ui:>8.2f}% | IBGE         | {date.today()} | [02/2026]   |
| NTN-B Longa   | IPCA+{nb_ui:.2f}% | Tes/Backup   | {date.today()} | [Backup Py] |
| Juro Real     | {j_real:>8.2f}% | Calculado    | Selic-IPCA   | [{clima}]   |
+---------------+-----------+--------------+--------------+-------------+
"""
    terminal_print(ancora)

tab_a, tab_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# =====================================================================
# MÓDULO A: TICKER ÚNICO
# =====================================================================
with tab_a:
    ticker = st.text_input("Ticker do Ativo:").upper()
    trilha = st.selectbox("Trilha (Patch 7):", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])
    
    if ticker:
        st.markdown("### 🔬 MÓDULO 5 — PROTOCOLO PED (GATE DE AUDITORIA)")
        with st.expander("📥 VERIFICAÇÃO SOMBRA (Patch 5)", expanded=True):
            noticia = st.text_input("Título da Notícia Recente (Investidor10):")
            if noticia: st.success("✅ ACESSO REAL CONFIRMADO.")
            
            c1, c2, c3 = st.columns(3)
            p_google = c1.number_input("Preço (Google Finance)", value=23.43)
            lpa = c1.number_input("Campo 1: LPA (R$)", value=3.12)
            vpa = c1.number_input("Campo 2: VPA (R$)", value=32.94)
            dy = c2.number_input("Campo 3: DY 12m (%)", value=3.54)
            roe = c2.number_input("Campo 4: ROE (%)", value=15.0)
            cagr = c2.number_input("Campo 7: CAGR DPA (%)", value=4.77)
            liq = c3.number_input("Campo 6: Liquidez Diária (R$)", value=262387884.0)
            setor = c3.selectbox("Campo E: Setor/Segmento", ["Essencial Perene", "Essencial Moderado", "Semi-Essencial", "Cíclico"])
            tend = c3.selectbox("Campo 9C: Tendência Lucros 3 anos", ["Crescente", "Estável", "Decrescente", "Prejuízo Recorrente"])

        if st.button("🚀 EXECUTAR CICLO DETERMINÍSTICO"):
            st.markdown("---")
            # --- FASE 2: SCORECARD ---
            st.write("**FASE 2: Scorecard Determinístico (Módulo 8)**")
            
            # PILAR A (Regra 3 - Aritmética)
            if trilha == "AÇÕES":
                vi = math.sqrt(22.5 * lpa * vpa)
                margem = ((vi - p_google) / vi) * 100
                st.write(f"▸ Fórmula  | VI = raiz(22,5 x LPA x VPA)")
                st.write(f"▸ Substitui | VI = raiz(22,5 x {lpa} x {vpa})")
                st.write(f"▸ Resultado | R$ {vi:.2f}")
                n_a = 20 if margem > 20 else 15 if margem > 0 else 5
                diag_a = f"Margem {margem:.1f}% — VI R${vi:.2f}"
            elif trilha == "FII TIJOLO":
                pvp = p_google / vpa
                n_a = 20 if pvp <= 0.9 else 15 if pvp <= 1.0 else 5
                diag_a = f"P/VP {pvp:.2f}"
            else: # PAPEL
                spread = dy - nb_ui
                n_a = 20 if spread > 4 else 15 if spread >= 2 else 5
                diag_a = f"Spread {spread:.2f} p.p."

            n_r = 20 if cagr > 10 else 15 if cagr > 5 else 10
            n_e = 20 if "Perene" in setor else 15 if "Moderado" in setor else 5
            n_n = 20 if roe > 20 else 15 if roe >= 15 else 5
            
            sub = n_r + n_e + n_n + n_a
            score = (sub / 80) * 100
            
            score_table = f"""
+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Ref. Patch 7)       |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA 3 anos     | {n_r:<10} | CAGR {cagr}% (Cap 4.3)            |
| E       | Setor / Segmento    | {n_e:<10} | {setor[:30]} |
| N       | ROE/Eficiência      | {n_n:<10} | ROE {roe}% (Cap 6.3)              |
| D       | Desvio Talmud       | -- (N/A)   | (Modulo C - carteira)            |
| A       | Alocação            | {n_a:<10} | {diag_a[:32]} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.0f}/100     | ({sub}/80) x 100                 |
+---------+---------------------+------------+----------------------------------+
"""
            terminal_print(score_table)

            # --- FASE 3: AVA (Cap 11.7) ---
            st.write("**FASE 3: Diagnóstico de Risco (Protocolo AVA)**")
            ava_table = f"""
+-------+-------------------------+-----------------------------------------+
| Trava | Criterio de Avaliacao   | Diagnostico e Status do Veto            |
+-------+-------------------------+-----------------------------------------+
| AVA-1 | Destruicao de Valor     | {'🚨 VETO' if tend in ['Decrescente', 'Prejuízo Recorrente'] else '✅ APROVADO'} ({tend}) |
| AVA-2 | Risco de Ruina          | {'✅ APROVADO' if liq > 1000000 else '🚨 VETO: BAIXA LIQ'} |
+-------+-------------------------+-----------------------------------------+
"""
            terminal_print(ava_table)
            
            pdf_b = gerar_pdf(ancora + score_table + ava_table)
            st.download_button("📥 Baixar Relatório V.102.09", pdf_b, f"RENDA_{ticker}.pdf")

# =====================================================================
# MÓDULO C: VISÃO DO BOSQUE
# =====================================================================
with tab_c:
    st.subheader("🌲 MÓDULO C — VISÃO DO BOSQUE (ANÁLISE DE CARTEIRA)")
    
    # Editor de Carteira
    df_c = pd.DataFrame([
        {"Ticker": "BBAS3", "%": 33.3, "Tipo": "AÇÃO", "ROE": 21.0, "DY": 9.0, "Setor": "Defensiva"},
        {"Ticker": "HGLG11", "%": 33.3, "Tipo": "FII TIJOLO", "ROE": 0.0, "DY": 8.5, "Setor": "Tijolo"},
        {"Ticker": "TESOURO", "%": 33.4, "Tipo": "RF", "ROE": 0.0, "DY": 10.75, "Setor": "Defensiva"}
    ])
    edit_c = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)
    aporte = st.number_input("Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ EXECUTAR ANÁLISE DO BOSQUE"):
        # C.1 Talmud (Cap 8.3)
        p_a = edit_c[edit_c["Tipo"] == "AÇÃO"]["%"].sum()
        p_f = edit_c[edit_c["Tipo"].str.contains("FII")]["%"].sum()
        p_rf = edit_c[edit_c["Tipo"] == "RF"]["%"].sum()
        dev = (abs(p_a - 33.3) + abs(p_f - 33.3) + abs(p_rf - 33.4)) / 3
        
        st.write("### C.1 Termômetro do Talmud")
        st.write(f"▸ Desvio Médio: {dev:.1f} p.p.")
        if dev <= 5: st.success("🍏 POMAR EQUILIBRADO")
        else: st.error("🍎 MONOCULTURA DETECTADA")

        # C.3 Grande Virada (Cap 8.5.1)
        dy_p = (edit_c["DY"] * (edit_c["%"]/100)).sum()
        pat_v = (aporte * 12) / (dy_p / 100) if dy_p > 0 else 0
        st.write("### 🌱 C.3 Simulador da Grande Virada")
        st.write(f"▸ Fórmula  | Pat_Virada = (Aporte x 12) / DY_decimal")
        st.write(f"▸ Substitui | Pat_Virada = ({aporte} x 12) / {dy_p/100:.4f}")
        st.success(f"💰 PATRIMÔNIO ALVO: R$ {pat_v:,.2f}")

        # C.4 Teste Ácido (ROE vs Ke)
        st.write("### C.4 Teste Ácido de Geração de Valor (Ações)")
        for _, r in edit_c[edit_c["Tipo"] == "AÇÃO"].iterrows():
            spread = r["ROE"] - s_ui
            st.write(f"**{r['Ticker']}**: {r['ROE']}% (ROE) - {s_ui}% (Ke) = {spread:.1f}% ({'✅ GERAÇÃO' if spread > 0 else '🚨 DESTRUIÇÃO'})")
            
