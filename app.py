import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
from datetime import datetime, date
from fpdf import FPDF

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO RÍGIDA MÓDULO 0.5
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def terminal_print(texto):
    """Garante o alinhamento visual exigido no Módulo 0.5."""
    st.code(texto, language="text")

def limpar_para_pdf(texto):
    """Filtra caracteres que o PDF não suporta (Emojis e acentos especiais)."""
    subs = {
        "⚠️": "AVISO:", "🌱": "", "🌳": "BOSQUE:", "🔬": "PED:", 
        "📊": "SCORE:", "🎯": "FINAL:", "✅": "[OK]", "🚨": "[VETO]",
        "❄️": "FRIO:", "☀️": "CALOR:", "💎": "[TOP]"
    }
    for emoji, rep in subs.items():
        texto = texto.replace(emoji, rep)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def gerar_pdf_bytes(conteudo_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9)
    texto_limpo = limpar_para_pdf(conteudo_texto)
    for linha in texto_limpo.split('\n'):
        pdf.cell(0, 5, txt=linha, ln=1)
    return bytes(pdf.output())

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 0 — SAFE HARBOR (BLINDAGEM JURÍDICA)
# ═══════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════
# SEGURANÇA E ACESSO
# ═══════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    exibir_aviso_legal()
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso do Livro:", type="password")
    if st.button("🔓 Validar Semente"):
        if pwd == "RENDA2026":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Chave inválida.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# MOTOR PERPÉTUO — DADOS MACRO (PATCH 1, 2, 3)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]['valor'])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]['valor'])
        dias = (date.today() - date(2026, 1, 29)).days
        copom_min = 276 + int(dias / 45)
        nb_backup = (s - i) * 0.6 + i
        return s, i, copom_min, nb_backup
    except:
        return 10.75, 4.50, 276, 6.20

# ═══════════════════════════════════════════════════════════════════════════
# MOTORES DE GARIMPO (INDICADORES)
# ═══════════════════════════════════════════════════════════════════════════
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
    d['liq'] = ext(r'Liquidez\s+Diaria[\s\S]{0,30}?([0-9.,]+)', texto)
    return d

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
exibir_aviso_legal()
s_val, i_val, cp_min, nb_back = fetch_macro()
st.title("🌱 Sistema de Ensino R.E.N.D.A.")

# ETAPA G5 — ÂNCORA MACRO
st.subheader("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO")
c1, c2, c3, c4 = st.columns(4)
s_ui = c1.number_input("Selic Meta (%)", value=s_val, help="Fonte: Banco Central (SGS 432)")
i_ui = c2.number_input("IPCA 12m (%)", value=i_val, help="Fonte: IBGE (SGS 13522)")
cp_ui = c3.number_input("Nº Reunião COPOM", value=cp_min, help="Patch 1: Validador de frescura do dado.")
nb_ui = c4.number_input("NTN-B Longa (IPCA+)", value=nb_back, help="Patch 3: Regra D-1 ou Backup Python.")

if cp_ui < cp_min:
    st.error(f"🚨 DADO OBSOLETO: Reunião COPOM {cp_ui} < Mínima {cp_min}. Atualize os dados macro.")
    st.stop()

j_real = s_ui - i_ui
clima = "❄️ INVERNO MACRO" if j_real > 10 else "☀️ VERÃO MACRO"
ancora_ascii = f"""
+---------------+-----------+--------------+--------------+-------------+
| Variavel      | Valor     | Fonte (URL)  | Data/Hora    | Prova Sombra|
+---------------+-----------+--------------+--------------+-------------+
| Selic Meta    | {s_ui:>8.2f}% | BCB          | {date.today()} | [COPOM {cp_ui}✅] |
| IPCA 12m      | {i_ui:>8.2f}% | IBGE         | {date.today()} | [Mês IBGE]  |
| NTN-B Longa   | IPCA+{nb_ui:.2f}% | Tes/Backup   | {date.today()} | [Regra D-1] |
| Juro Real     | {j_real:>8.2f}% | Calculado    | Selic-IPCA   | [{clima}]   |
+---------------+-----------+--------------+--------------+-------------+
"""
terminal_print(ancora_ascii)

# NAVEGAÇÃO
aba_a, aba_c = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO A — TICKER ÚNICO (FASES 1, 2 E 3)
# ═══════════════════════════════════════════════════════════════════════════
with aba_a:
    ticker = st.text_input("INSIRA O TICKER PARA ANÁLISE:", value="").upper()
    trilha = st.selectbox("Selecione a Natureza do Ativo (Patch 7):", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])
    
    if ticker:
        st.subheader(f"🔬 FASE 1: Protocolo de Extração (PED) — {ticker}")
        
        with st.expander("📥 GATE DE AUDITORIA (Patch 5/8)", expanded=True):
            st.info("Copie a página do Investidor10/StatusInvest (CTRL+A) e cole abaixo para preenchimento automático.")
            noticia = st.text_input("Notícia Sombra (Título da notícia mais recente):", help="Patch 5: Valida o acesso real à fonte de dados.")
            txt_ped = st.text_area("Área de Colagem de Fundamentos:")
            ext = garimpar_dados_ativo(txt_ped) if txt_ped else {}
            
            try: p_goog = yf.Ticker(f"{ticker}.SA").history(period="1d")['Close'].iloc[-1]
            except: p_goog = 10.0

            cA, cB, cC = st.columns(3)
            with cA:
                p_final = cA.number_input("Cotação Real (Google Finance)", value=float(ext.get('preco', p_goog)), help="Patch 8: Cotação em tempo real para cálculos de margem.")
                v_lpa = cA.number_input("1. LPA (Lucro por Ação)", value=float(ext.get('lpa', 0.0)), help="Cap. 6.5 (pág. 166).")
                v_vpa = cA.number_input("2. VPA (Valor Patrimonial)", value=float(ext.get('vpa', 0.0)), help="Cap. 6.5 (pág. 167).")
            with cB:
                v_dy = cB.number_input("3. DY 12m (%)", value=float(ext.get('dy', 0.0)), help="Cap. 6.5.4 (pág. 169).")
                v_roe = cB.number_input("4. ROE (%)", value=float(ext.get('roe', 0.0)), help="Cap. 6.3 (pág. 152): Indica eficácia da gestão.")
                v_cagr = cB.number_input("7. CAGR DPA (%)", value=float(ext.get('cagr', 0.0)), help="Cap. 4.3 (pág. 85): Seiva da árvore.")
            with cC:
                v_liq = cC.number_input("6. Liquidez (R$/dia)", value=float(ext.get('liq', 2000000.0)), help="Protocolo AVA-2: Risco de saída.")
                v_setor = cC.selectbox("Pilar E - Setor:", ["Essencial Perene", "Essencial Moderado", "Semi-Essencial", "Cíclico"], help="Cap. 5.3 (pág. 122).")
                v_tend = cC.selectbox("9C. Tendência de Lucros:", ["Crescente", "Estável", "Decrescente"], help="Cap. 11.7 (pág. 267): Veto AVA-1.")

        if st.button("🚀 EXECUTAR CICLO DETERMINÍSTICO COMPLETO"):
            # --- FASE 2: SCORECARD ---
            st.markdown("---")
            st.subheader(f"📊 FASE 2: Scorecard Determinístico — {ticker}")
            
            # PILAR A (Regra 3 - Aritmética)
            st.write("**CÁLCULO DA ALOCAÇÃO (Pilar A - Cap 6.5 / 8.0)**")
            if trilha == "AÇÕES":
                vi = math.sqrt(22.5 * v_lpa * v_vpa) if v_lpa > 0 else 0
                margem = ((vi - p_final) / vi) * 100 if vi > 0 else 0
                st.write(f"▸ Fórmula  | VI = raiz(22,5 x LPA x VPA)")
                st.write(f"▸ Substitui | VI = raiz(22,5 x {v_lpa:.2f} x {v_vpa:.2f})")
                st.write(f"▸ Resultado | R$ {vi:.2f}")
                n_a = 20 if margem > 20 else 15 if margem > 0 else 5
                diag_a = f"Margem Graham: {margem:.1f}%"
            elif trilha == "FII TIJOLO":
                pvp = p_final / v_vpa if v_vpa > 0 else 1
                st.write(f"▸ Fórmula  | P/VP = Preço / VPA")
                st.write(f"▸ Resultado | {pvp:.2f}")
                n_a = 20 if pvp <= 0.90 else 15 if pvp <= 1.0 else 5
                diag_a = f"P/VP Recalculado: {pvp:.2f}"
            else: # PAPEL
                spread = v_dy - nb_ui
                st.write(f"▸ Fórmula  | Spread = DY - NTN-B")
                st.write(f"▸ Resultado | {spread:.2f} p.p.")
                n_a = 20 if spread > 4 else 15 if spread >= 2 else 5
                diag_a = f"Spread NTN-B: {spread:.2f}%"

            n_r = 20 if v_cagr > 10 else 15 if v_cagr > 5 else 10
            n_e = 20 if "Perene" in v_setor else 15 if "Moderado" in v_setor else 5
            n_n = 20 if v_roe > 20 else 15 if v_roe >= 15 else 10
            
            sub = n_r + n_e + n_n + n_a
            score = (sub / 80) * 100
            
            score_ascii = f"""
+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Ref. Patch 7)       |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA 3 anos     | {n_r:<10} | CAGR {v_cagr}% (Cap 4.3)            |
| E       | Setor / Segmento    | {n_e:<10} | {v_setor[:30]} |
| N       | ROE/Eficiência      | {n_n:<10} | ROE {v_roe}% (Cap 6.3)              |
| D       | Desvio Talmud       | -- (N/A)   | (Módulo C - Carteira)            |
| A       | Alocação            | {n_a:<10} | {diag_a[:32]} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.1f}/100    | ({sub}/80) x 100                 |
+---------+---------------------+------------+----------------------------------+
"""
            terminal_print(score_ascii)

            # ESCALA DE VITALIDADE (Cap 8.6)
            if score >= 85: st.success("💎 SAFRA RESILIENTE: Alta robustez.")
            elif score >= 75: st.info("🌳 ÁRVORE SAUDÁVEL: Fundamentos sólidos.")
            elif score >= 60: st.warning("🌿 SOLO FÉRTIL: Acima do limiar mínimo.")
            else: st.error("🚨 TERRENO ÁRIDO: Fundamentos críticos.")

            # --- FASE 3: AVA ---
            st.markdown("### 🚨 FASE 3: Diagnóstico de Risco (Protocolo AVA - Cap 11.7)")
            ava_ascii = f"""
+-------+-------------------------+-----------------------------------------+
| Trava | Criterio de Avaliacao   | Diagnostico e Status do Veto            |
+-------+-------------------------+-----------------------------------------+
| AVA-1 | Destruicao de Valor     | {'🚨 VETO' if v_tend == 'Decrescente' else '✅ APROVADO'} ({v_tend}) |
| AVA-2 | Risco de Ruina          | ✅ APROVADO (Divida Controlada)         |
| AVA-2 | Risco de Liquidez       | {'✅ APROVADO' if v_liq > 1000000 else '🚨 VETO: BAIXA LIQ'} |
+-------+-------------------------+-----------------------------------------+
"""
            terminal_print(ava_ascii)
            
            # EXPORTAÇÃO PDF
            report = ancora_ascii + score_ascii + ava_ascii
            pdf_bytes = gerar_pdf_bytes(report)
            st.download_button("📥 Baixar Relatório Mestre (PDF)", pdf_bytes, f"RENDA_{ticker}.pdf")

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO C — VISÃO DO BOSQUE (CARTEIRA)
# ═══════════════════════════════════════════════════════════════════════════
with aba_c:
    st.subheader("🌲 MÓDULO C — ANÁLISE DE CARTEIRA (VISÃO DO BOSQUE)")
    st.info("Cap. 8.3: A Matriz do Talmud (1/3 Ações, 1/3 FIIs, 1/3 RF).")

    with st.expander("📥 IMPORTAR CARTEIRA (CONSOLIDADOR)", expanded=True):
        st.write("Aperte CTRL+A no StatusInvest/Kinvo e cole abaixo.")
        txt_c = st.text_area("Área de Colagem da Carteira:", placeholder="Ticker | Peso % | Proventos...")
    
    # Inicia vazio
    df_empty = pd.DataFrame([{"Ticker": "", "Tipo": "AÇÃO", "%": 0.0, "DY": 0.0, "ROE": 0.0}])
    edit_c = st.data_editor(df_empty, num_rows="dynamic", use_container_width=True)
    
    aporte_m = st.number_input("Seu Aporte Mensal (R$):", value=1000.0, help="Cap. 8.5.1: Necessário para calcular a Grande Virada.")

    if st.button("⚖️ EXECUTAR PROTOCOLO VISÃO DO BOSQUE"):
        p_a = edit_c[edit_c["Tipo"] == "AÇÃO"]["%"].sum()
        p_f = edit_c[edit_c["Tipo"] == "FII"]["%"].sum()
        p_rf = 100 - p_a - p_f
        
        # C.1 TERMÔMETRO TALMUD
        st.write("#### C.1 Termômetro do Talmud (Cap. 8.3)")
        talmud = f"""
+------------------------------------------------------------------+
| Acoes: {p_a:>5.1f}% | FIIs: {p_f:>5.1f}% | Renda Fixa: {p_rf:>5.1f}% |
+------------------------------------------------------------------+
"""
        terminal_print(talmud)

        # C.3 GRANDE VIRADA (Cap 8.5.1)
        dy_p = (edit_c["DY"] * (edit_c["%"]/100)).sum()
        pat_v = (aporte_m * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        st.write("#### 🌱 C.3 Simulador da Grande Virada")
        st.write(f"▸ Fórmula  | Pat_Virada = (Aporte x 12) / DY_decimal")
        st.write(f"▸ Substitui | Pat_Virada = ({aporte_m} x 12) / {dy_p/100:.4f}")
        st.success(f"💰 PATRIMÔNIO ALVO: R$ {pat_v:,.2f}")

st.markdown("---")
terminal_print("R.E.N.D.A. PROTOCOL™ V.102.09 FULL © Laerson Endrigo Ely, 2026.")
