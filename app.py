import streamlit as st
import pandas as pd
import requests
import math
import re
from datetime import date
from fpdf import FPDF

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def limpar_para_pdf(texto):
    """Remove emojis e caracteres que travam o gerador de PDF padrão."""
    # Substitui emojis por equivalentes em texto ou remove
    substituicoes = {
        "⚠️": "AVISO:", "🌱": "", "🌳": "BOSQUE:", "🔬": "PED:", 
        "📊": "SCORE:", "🎯": "FINAL:", "✅": "[OK]", "🚨": "[VETO]",
        "❄️": "FRIO:", "☀️": "CALOR:", "💎": "[TOP]"
    }
    for emoji, rep in substituicoes.items():
        texto = texto.replace(emoji, rep)
    # Remove qualquer outro caractere não-latin1
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def gerar_pdf(conteudo_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9) # Fonte monoespaçada para tabelas
    texto_limpo = limpar_para_pdf(conteudo_texto)
    for linha in texto_limpo.split('\n'):
        pdf.cell(0, 5, txt=linha, ln=True)
    return pdf.output(dest='S')

# --- SEGURANÇA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso do Livro:", type="password")
    if st.button("Validar Semente"):
        if pwd == "RENDA2026":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Chave inválida.")
    st.stop()

# --- MOTOR DE DADOS MACRO ---
@st.cache_data(ttl=3600)
def buscar_macro():
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]['valor'])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]['valor'])
        return s, i
    except: return 10.50, 4.50

def garimpar_dados(texto):
    d = {}
    def ext(p, t):
        m = re.search(p, t, re.IGNORECASE)
        return float(m.group(1).replace('.', '').replace(',', '.')) if m else None
    d['preco'] = ext(r'(?:VALOR ATUAL|Cotação|Preço)[\s\S]{0,30}?R\$?\s*([0-9.,]+)', texto)
    d['lpa'] = ext(r'LPA[\s\S]{0,20}?([0-9.,]+)', texto)
    d['vpa'] = ext(r'VPA[\s\S]{0,20}?([0-9.,]+)', texto)
    d['dy'] = ext(r'(?:Dividend Yield|DY)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    d['roe'] = ext(r'ROE[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    d['cagr'] = ext(r'CAGR\s+(?:LUCROS|DPA)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    return d

# --- INTERFACE ---
st.title("🌱 Sistema de Ensino R.E.N.D.A.")
st.caption("R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL © Laerson Endrigo Ely, 2026.")

aba1, aba2 = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# =====================================================================
# MÓDULO A: TICKER ÚNICO
# =====================================================================
with aba1:
    selic, ipca = buscar_macro()
    ticker = st.text_input("INSIRA O TICKER PARA ANÁLISE:", value="BBAS3").upper()
    
    with st.expander("📥 MÓDULO DE ENTRADA (PED)", expanded=True):
        txt = st.text_area("Área de Colagem (Investidor10):", key="ped_input")
        extraidos = garimpar_dados(txt) if txt else {}
        
        c1, c2, c3 = st.columns(3)
        preco = c1.number_input("Preço Atual (R$)", value=extraidos.get('preco', 23.41))
        f_lpa = c1.number_input("LPA (R$)", value=extraidos.get('lpa', 2.39))
        f_vpa = c1.number_input("VPA (R$)", value=extraidos.get('vpa', 33.02))
        f_dy = c2.number_input("DY 12m (%)", value=extraidos.get('dy', 3.54))
        f_cagr = c2.number_input("CAGR DPA 3a (%)", value=extraidos.get('cagr', 4.77))
        f_roe = c2.number_input("ROE (%)", value=extraidos.get('roe', 7.24))
        f_setor = c3.selectbox("Setor:", ["Bancos — Essencial Perene", "Energia — Essencial Perene", "Cíclico", "FII"])
        f_liq = c3.number_input("Liquidez (R$/dia)", value=262387884.0)
        f_tend = c3.selectbox("Tendência Lucros (AVA-1):", ["Crescente/Estável", "Decrescente"])

    if st.button("🚀 EXECUTAR CICLO DETERMINÍSTICO"):
        # Cálculos Graham
        vi = math.sqrt(22.5 * f_lpa * f_vpa) if f_lpa > 0 else 0
        margem = ((vi - preco) / vi) * 100 if vi > 0 else 0
        
        # Lógica Scorecard
        nota_r = 20 if f_cagr > 10 else 15 if f_cagr > 5 else 10
        nota_e = 20 if "Essencial" in f_setor else 10
        nota_n = 20 if f_roe > 15 else 15 if f_roe > 10 else 10
        nota_a = 20 if margem > 20 else 15 if margem > 0 else 5
        
        subtotal = nota_r + nota_e + nota_n + nota_a
        score = (subtotal / 80) * 100
        
        juro_real = selic - ipca
        alerta_macro = "INVERNO MACRO" if juro_real > 10 else "VERAO MACRO"
        
        relatorio = f"""
+----------------------------------------------------------------------+
| AVISO LEGAL -- O Metodo R.E.N.D.A. V.102.09 FULL                      |
+----------------------------------------------------------------------+
FASE 2: Scorecard Deterministico -- {ticker}

CALCULO DA MARGEM DE SEGURANCA (Pilar A)
- Formula  | VI = raiz(22,5 x LPA x VPA)
- Resultado| R$ {vi:.2f}
- Margem   | {margem:.2f}%

+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico                      |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA 3 anos     | {nota_r:<10} | CAGR {f_cagr}%                       |
| E       | Setor / Segmento    | {nota_e:<10} | {f_setor[:30]} |
| N       | ROE/Vac/Inadim      | {nota_n:<10} | ROE {f_roe}%                         |
| D       | Desvio Talmud       | -- (N/A)   | (Modulo A - Ticker Unico)        |
| A (Ac.) | Graham              | {nota_a:<10} | Margem {margem:.2f}% -- VI R${vi:.2f} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.1f}/100    | ( {subtotal} / 80 ) x 100            |
+---------+---------------------+------------+----------------------------------+

FASE 3: Diagnostico de Risco (Protocolo AVA)
- AVA-1 (Lucros): {'APROVADO' if f_tend != 'Decrescente' else 'VETO: QUEDA LUCRO'}
- AVA-2 (Ruina): APROVADO
- AVA-2 (Liquidez): {'APROVADO' if f_liq > 1000000 else 'VETO: BAIXA LIQ'}

Alerta Climatico: {alerta_macro}. Juro Real: {juro_real:.2f}%
SINTESE: Score {score:.1f}/100. Margem {margem:.2f}%.
"""
        st.code(relatorio, language="text")
        
        pdf_bytes = gerar_pdf(relatorio)
        st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"RENDA_{ticker}.pdf", mime="application/pdf")

# =====================================================================
# MÓDULO C: VISÃO DO BOSQUE
# =====================================================================
with aba2:
    st.subheader("🌲 MÓDULO C — ANÁLISE DE CARTEIRA")
    
    with st.expander("📥 Importar da Corretora"):
        txt_cart = st.text_area("Cole aqui sua lista de ativos:", key="carteira_input")
        ticks = re.findall(r'\b([A-Z]{4}[1-9]{1,2})\b', txt_cart.upper()) if txt_cart else []
    
    df_base = pd.DataFrame([{"Ticker": t, "Tipo": "Ações" if t[-1] in '34' else "FIIs", "Peso %": 10.0, "DY %": 8.0} for t in set(ticks)])
    if df_base.empty: df_base = pd.DataFrame([{"Ticker": "BBAS3", "Tipo": "Ações", "Peso %": 50.0, "DY %": 9.0}, {"Ticker": "HGLG11", "Tipo": "FIIs", "Peso %": 50.0, "DY %": 8.0}])
    
    edit_df = st.data_editor(df_base, num_rows="dynamic", use_container_width=True)
    aporte = st.number_input("Seu Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ Executar Visão do Bosque"):
        perc_acoes = edit_df[edit_df["Tipo"] == "AÇÕES"]["Peso %"].sum() if "AÇÕES" in edit_df["Tipo"].values else edit_df[edit_df["Tipo"] == "Ações"]["Peso %"].sum()
        perc_fiis = edit_df[edit_df["Tipo"] == "FIIs"]["Peso %"].sum()
        perc_rf = 100 - perc_acoes - perc_fiis
        
        dy_p = (edit_df["DY %"] * (edit_df["Peso %"]/100)).sum()
        pat_v = (aporte * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        rel_c = f"""
🌳 MODULO C -- RELATORIO DE CARTEIRA (VISAO DO BOSQUE)
------------------------------------------------------
C.1 TERMOMETRO DO TALMUD (EQUILIBRIO)
- Acoes: {perc_acoes:.1f}% (Alvo 33.3%)
- FIIs:  {perc_fiis:.1f}% (Alvo 33.3%)
- R.Fixa: {perc_rf:.1f}% (Alvo 33.3%)

C.3 SIMULADOR DA GRANDE VIRADA
Para igualar seu aporte mensal de R$ {aporte:,.2f}:
- DY Medio Ponderado: {dy_p:.2f}%
- PATRIMONIO ALVO: R$ {pat_v:,.2f}
"""
        st.code(rel_c, language="text")
        
        pdf_c = gerar_pdf(rel_c)
        st.download_button(label="📥 Baixar Análise de Carteira", data=pdf_c, file_name="RENDA_Carteira.pdf", mime="application/pdf")
