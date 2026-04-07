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
    """Alinhamento visual fixo conforme Módulo 0.5"""
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

# --- MOTOR MACRO (PATCH 1, 2, 3) ---
@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]['valor'])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]['valor'])
        dias = (date.today() - date(2026, 1, 29)).days
        copom_min = 276 + int(dias / 45)
        return s, i, copom_min
    except:
        return 10.75, 4.50, 276

# --- MOTOR DE GARIMPO DE CARTEIRA (CONSOLIDADORES) ---
def garimpar_carteira_completa(texto):
    """Extrai Ticker e Porcentagem de textos de consolidadores."""
    linhas = texto.upper().split('\n')
    carteira = []
    for linha in linhas:
        ticker = re.search(r'\b([A-Z]{4}[1-9]{1,2})\b', linha)
        if ticker:
            t = ticker.group(1)
            # Procura porcentagem na linha
            percent = re.search(r'(\d+[.,]\d+|\d+)\s*%', linha)
            p = float(percent.group(1).replace(',', '.')) if percent else 0.0
            tipo = "AÇÃO" if t[-1] in '3456' else "FII"
            carteira.append({"Ticker": t, "Tipo": tipo, "%": p, "DY": 0.0, "ROE": 0.0, "LTV/Div": 0.0})
    return carteira

# --- INÍCIO DA INTERFACE ---
exibir_aviso_legal()
st.title("🌱 Sistema de Ensino R.E.N.D.A.")
s_atual, i_atual, copom_m = fetch_macro()

# --- ETAPA G5: ÂNCORA MACRO ---
st.subheader("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO")
c1, c2, c3 = st.columns(3)
s_ui = c1.number_input("Selic Meta (%)", value=s_atual)
i_ui = c2.number_input("IPCA 12m (%)", value=i_atual)
cp_ui = c3.number_input("Nº Reunião COPOM", value=copom_m)

if cp_ui < copom_m:
    st.error(f"🚨 DADO OBSOLETO: COPOM {cp_ui} < {copom_m}")
    st.stop()

j_real = s_ui - i_ui
clima = "❄️ INVERNO MACRO" if j_real > 10 else "☀️ VERÃO MACRO"
ancora_text = f"""
+---------------+-----------+--------------+--------------+-------------+
| Variavel      | Valor     | Fonte (URL)  | Data/Hora    | Prova Sombra|
+---------------+-----------+--------------+--------------+-------------+
| Selic Meta    | {s_ui:>8.2f}% | BCB          | {date.today()} | [COPOM {cp_ui}✅] |
| IPCA 12m      | {i_ui:>8.2f}% | IBGE         | {date.today()} | [02/2026]   |
| Juro Real     | {j_real:>8.2f}% | Calculado    | Selic-IPCA   | [{clima}]   |
+---------------+-----------+--------------+--------------+-------------+
"""
terminal_print(ancora_text)

tab_a, tab_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# =====================================================================
# MÓDULO A (SIMPLIFICADO PARA FOCO NO C)
# =====================================================================
with tab_a:
    st.write("Análise individual de ativos com Protocolo PED e AVA.")
    st.info("Utilize este módulo para auditoria profunda de uma única 'árvore'.")

# =====================================================================
# MÓDULO C: VISÃO DO BOSQUE (AQUI ESTÁ A CORREÇÃO)
# =====================================================================
with tab_c:
    st.subheader("🌲 MÓDULO C — ANÁLISE DE CARTEIRA (VISÃO DO BOSQUE)")
    st.markdown("**Cap. 8.3 — A Matriz de Alocação:** '1/3 FIIs, 1/3 Ações, 1/3 RF. Talmud.'")

    with st.expander("📥 IMPORTAÇÃO POR COLAGEM (StatusInvest / Kinvo / Corretora)", expanded=True):
        st.write("Aperte CTRL+A na tela do seu consolidador, copie e cole abaixo.")
        txt_c = st.text_area("Área de Colagem da Carteira:", height=150, placeholder="Cole aqui o texto da sua carteira...")
        
        # Garimpo automático
        dados_importados = garimpar_carteira_completa(txt_c) if txt_c else []
        if dados_importados:
            st.success(f"✅ {len(dados_importados)} ativos detectados com sucesso!")

    # TABELA DE EDIÇÃO (Inicia vazia ou com importação)
    if not dados_importados:
        # Tabela inicia apenas com uma linha vazia para instrução
        df_init = pd.DataFrame([{"Ticker": "", "Tipo": "AÇÃO", "%": 0.0, "DY": 0.0, "ROE": 0.0, "LTV/Div": 0.0}])
    else:
        df_init = pd.DataFrame(dados_importados)

    st.write("### 📝 Ajuste Fino da Carteira")
    edit_c = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)
    
    c_inv, c_ap = st.columns(2)
    patrimonio_total = c_inv.number_input("Patrimônio Total Atual (R$):", value=10000.0)
    aporte_mensal = c_ap.number_input("Aporte Mensal Médio (R$):", value=1000.0)

    if st.button("⚖️ EXECUTAR PROTOCOLO VISÃO DO BOSQUE"):
        st.markdown("---")
        # C.1 — TERMÔMETRO DO TALMUD (Cap. 8.3)
        p_acoes = edit_c[edit_c["Tipo"] == "AÇÃO"]["%"].sum()
        p_fiis = edit_c[edit_c["Tipo"] == "FII"]["%"].sum()
        p_rf = 100 - p_acoes - p_fiis
        dev = (abs(p_acoes - 33.3) + abs(p_fiis - 33.3) + abs(p_rf - 33.4)) / 3

        st.write("#### C.1 — Termômetro do Talmud (Pilar D)")
        talmud_res = f"""
+------------------------------------------------------------------+
| Acoes: {p_acoes:>5.1f}% | FIIs: {p_fiis:>5.1f}% | Renda Fixa: {p_rf:>5.1f}% |
+------------------------------------------------------------------+
▸ Desvio Médio Talmud: {dev:.1f} p.p.
▸ Diagnóstico: {'🍏 POMAR EQUILIBRADO' if dev <= 5 else '🍋 DESEQUILÍBRIO' if dev <= 15 else '🍎 MONOCULTURA'}
"""
        terminal_print(talmud_res)

        # C.3 — 🌱 SIMULADOR DA GRANDE VIRADA (Cap. 8.5.1)
        dy_p = (edit_c["DY"] * (edit_c["%"]/100)).sum()
        pat_v = (aporte_mensal * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        st.write("#### C.3 — 🌱 Simulador da Grande Virada")
        st.write(f"**O livro:** 'Quando a Renda Passiva supera os aportes.' (Cap. 8.5.1)")
        st.write(f"▸ Fórmula  | Pat_Virada = (Aporte x 12) / DY_decimal")
        st.write(f"▸ Substitui | Pat_Virada = ({aporte_mensal} x 12) / {dy_p/100:.4f}")
        st.success(f"💰 PATRIMÔNIO DA VIRADA: R$ {pat_v:,.2f}")

        # C.4 — TESTE ÁCIDO (ROE vs Ke)
        st.write("#### C.4 — Teste Ácido de Geração de Valor (ROE vs Ke)")
        st.write(f"**O livro:** 'ROE alto indica que a gestão é eficaz.' (Cap. 6.3)")
        for _, r in edit_c[edit_c["Tipo"] == "AÇÃO"].iterrows():
            spread = r["ROE"] - s_ui
            st.write(f"**{r['Ticker']}**: {r['ROE']}% (ROE) - {s_ui}% (Ke) = {spread:.1f}% ({'✅ GERAÇÃO' if spread > 0 else '🚨 DESTRUIÇÃO'})")

        # EXPORTAÇÃO
        relatorio_completo = ancora_text + talmud_res + f"\nGRANDE VIRADA: R$ {pat_v:,.2f}"
        pdf_bytes = gerar_pdf_bytes(relatorio_completo)
        st.download_button("📥 Baixar Relatório do Bosque (PDF)", pdf_bytes, "RENDA_Carteira.pdf")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL © Laerson Endrigo Ely, 2026.")
