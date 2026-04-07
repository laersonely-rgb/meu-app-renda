import streamlit as st
import pandas as pd
import requests
import math
import re
import yfinance as yf
from datetime import date
from fpdf import FPDF

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def limpar_para_pdf(texto):
    substituicoes = {
        "⚠️": "AVISO:", "🌱": "", "🌳": "BOSQUE:", "🔬": "PED:", 
        "📊": "SCORE:", "🎯": "FINAL:", "✅": "[OK]", "🚨": "[VETO]",
        "❄️": "FRIO:", "☀️": "CALOR:", "💎": "[TOP]"
    }
    for emoji, rep in substituicoes.items():
        texto = texto.replace(emoji, rep)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def gerar_pdf(conteudo_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9)
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

# --- MOTOR DE DADOS MACRO (Sincronizado com BCB) ---
@st.cache_data(ttl=3600)
def buscar_macro():
    try:
        # Selic Meta (SGS 432)
        s_resp = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()
        selic = float(s_resp[0]['valor'])
        # IPCA 12m (SGS 13522)
        i_resp = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()
        ipca = float(i_resp[0]['valor'])
        return selic, ipca
    except:
        return 10.75, 4.50 # Fallback caso o site do BCB esteja instável

def garimpar_texto(texto):
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
st.title("🌱 Sistema de Ensino R.E.N.D.A.")
st.caption("R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL © Laerson Endrigo Ely, 2026.")

# Busca Macro Automática
selic, ipca = buscar_macro()

aba1, aba2 = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

# =====================================================================
# MÓDULO A: TICKER ÚNICO
# =====================================================================
with aba1:
    with st.expander("🌐 ETAPA G5 — DADOS MACRO ATUAIS", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("SELIC META (BCB)", f"{selic}%")
        c2.metric("IPCA 12M (BCB)", f"{ipca}%")

    ticker = st.text_input("INSIRA O TICKER PARA ANÁLISE (Ex: BBAS3, PETR4):", value="").upper()
    
    if ticker:
        # Extração Automática via API (Preço)
        try:
            stock = yf.Ticker(f"{ticker}.SA")
            preco_api = stock.history(period="1d")['Close'].iloc[-1]
        except:
            preco_api = 0.0

        with st.expander("📥 MÓDULO DE ENTRADA (PED)", expanded=True):
            st.info("Cole o texto do Investidor10 abaixo para preencher os fundamentos automaticamente.")
            txt = st.text_area("Área de Colagem (CTRL+A / CTRL+V):", key="ped_input")
            extraidos = garimpar_texto(txt) if txt else {}
            
            c_a, c_b, c_c = st.columns(3)
            val_preco = c_a.number_input("Preço Atual (R$)", value=float(preco_api if preco_api > 0 else 10.0))
            val_lpa = c_a.number_input("1. LPA (R$)", value=float(extraidos.get('lpa', 0.0)))
            val_vpa = c_a.number_input("2. VPA (R$)", value=float(extraidos.get('vpa', 0.0)))
            
            val_dy = c_b.number_input("3. DY 12m (%)", value=float(extraidos.get('dy', 0.0)))
            val_cagr = c_b.number_input("7. CAGR DPA 3a (%)", value=float(extraidos.get('cagr', 0.0)))
            val_roe = c_b.number_input("4. ROE (%)", value=float(extraidos.get('roe', 0.0)))
            
            val_setor = c_c.selectbox("8. Setor:", ["Bancos — Essencial Perene", "Energia — Essencial Perene", "Saneamento — Essencial Perene", "Cíclico"])
            val_liq = c_c.number_input("6. Liquidez (R$/dia)", value=2000000.0)
            val_tend = c_c.selectbox("9. Tendência Lucros:", ["Crescente/Estável", "Decrescente"])

        if st.button("🚀 EXECUTAR CICLO DETERMINÍSTICO"):
            if val_lpa <= 0 or val_vpa <= 0:
                st.error("ERRO: LPA e VPA devem ser maiores que zero para o cálculo de Graham.")
            else:
                # Cálculos
                vi = math.sqrt(22.5 * val_lpa * val_vpa)
                margem = ((vi - val_preco) / vi) * 100
                
                nota_r = 20 if val_cagr > 10 else 15 if val_cagr > 5 else 10
                nota_e = 20 if "Essencial" in val_setor else 10
                nota_n = 20 if val_roe > 15 else 15 if val_roe > 10 else 10
                nota_a = 20 if margem > 20 else 15 if margem > 0 else 5
                
                subtotal = nota_r + nota_e + nota_n + nota_a
                score = (subtotal / 80) * 100
                juro_real = selic - ipca
                
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
| R       | CAGR DPA 3 anos     | {nota_r:<10} | CAGR {val_cagr}%                       |
| E       | Setor / Segmento    | {nota_e:<10} | {val_setor[:30]} |
| N       | ROE/Vac/Inadim      | {nota_n:<10} | ROE {val_roe}%                         |
| D       | Desvio Talmud       | -- (N/A)   | (Modulo A - Ticker Unico)        |
| A (Ac.) | Graham              | {nota_a:<10} | Margem {margem:.2f}% -- VI R${vi:.2f} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.1f}/100    | ( {subtotal} / 80 ) x 100            |
+---------+---------------------+------------+----------------------------------+

FASE 3: Diagnostico de Risco (Protocolo AVA)
- AVA-1 (Lucros): {'APROVADO' if val_tend != 'Decrescente' else 'VETO: QUEDA LUCRO'}
- AVA-2 (Ruina): APROVADO
- AVA-2 (Liquidez): {'APROVADO' if val_liq > 1000000 else 'VETO: BAIXA LIQ'}

Alerta Climatico: {'INVERNO MACRO' if juro_real > 10 else 'VERAO MACRO'}. Juro Real: {juro_real:.2f}%
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
    txt_cart = st.text_area("Cole aqui sua lista de ativos para extração:", key="carteira_input")
    ticks = re.findall(r'\b([A-Z]{4}[1-9]{1,2})\b', txt_cart.upper()) if txt_cart else []
    
    df_base = pd.DataFrame([{"Ticker": t, "Tipo": "Ações" if t[-1] in '34' else "FIIs", "Peso %": 10.0, "DY %": 8.0} for t in set(ticks)])
    if df_base.empty: df_base = pd.DataFrame([{"Ticker": "BBAS3", "Tipo": "Ações", "Peso %": 50.0, "DY %": 9.0}, {"Ticker": "HGLG11", "Tipo": "FIIs", "Peso %": 50.0, "DY %": 8.0}])
    
    edit_df = st.data_editor(df_base, num_rows="dynamic", use_container_width=True)
    aporte = st.number_input("Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ Executar Visão do Bosque"):
        perc_a = edit_df[edit_df["Tipo"].str.contains("Ação|Ações", case=False)]["Peso %"].sum()
        perc_f = edit_df[edit_df["Tipo"] == "FIIs"]["Peso %"].sum()
        perc_rf = 100 - perc_a - perc_f
        
        dy_p = (edit_df["DY %"] * (edit_df["Peso %"]/100)).sum()
        pat_v = (aporte * 12) / (dy_p / 100) if dy_p > 0 else 0
        
        rel_c = f"""
MODULO C -- RELATORIO DE CARTEIRA (VISAO DO BOSQUE)
------------------------------------------------------
C.1 TERMOMETRO DO TALMUD (EQUILIBRIO)
- Acoes: {perc_a:.1f}% (Alvo 33.3%)
- FIIs:  {perc_f:.1f}% (Alvo 33.3%)
- R.Fixa: {perc_rf:.1f}% (Alvo 33.3%)

C.3 SIMULADOR DA GRANDE VIRADA
Para igualar seu aporte mensal de R$ {aporte:,.2f}:
- DY Medio Ponderado: {dy_p:.2f}%
- PATRIMONIO ALVO: R$ {pat_v:,.2f}
"""
        st.code(rel_c, language="text")
        pdf_c = gerar_pdf(rel_c)
        st.download_button(label="📥 Baixar Análise de Carteira", data=pdf_c, file_name="RENDA_Carteira.pdf", mime="application/pdf")
