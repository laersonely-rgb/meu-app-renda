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
    """Filtra caracteres que o PDF não suporta (Emojis e acentos especiais)."""
    substituicoes = {
        "⚠️": "AVISO:", "🌱": "", "🌳": "BOSQUE:", "🔬": "PED:", 
        "📊": "SCORE:", "🎯": "FINAL:", "✅": "[OK]", "🚨": "[VETO]",
        "❄️": "FRIO:", "☀️": "CALOR:", "💎": "[TOP]"
    }
    for emoji, rep in substituicoes.items():
        texto = texto.replace(emoji, rep)
    # Remove caracteres não compatíveis com Latin-1
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def gerar_pdf_bytes(conteudo_texto):
    """Gera o PDF e retorna em formato de BYTES para o Streamlit."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9)
    texto_limpo = limpar_para_pdf(conteudo_texto)
    for linha in texto_limpo.split('\n'):
        pdf.cell(0, 5, txt=linha, ln=1)
    # Retorna os bytes do PDF
    return bytes(pdf.output())

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
        # Selic Meta (SGS 432)
        s_resp = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()
        selic = float(s_resp[0]['valor'])
        # IPCA 12m (SGS 13522)
        i_resp = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()
        ipca = float(i_resp[0]['valor'])
        return selic, ipca
    except:
        return 10.75, 4.50

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

selic, ipca = buscar_macro()

aba1, aba2 = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque"])

with aba1:
    with st.expander("🌐 ETAPA G5 — DADOS MACRO ATUAIS"):
        c1, c2 = st.columns(2)
        c1.metric("SELIC (BCB)", f"{selic}%")
        c2.metric("IPCA (BCB)", f"{ipca}%")

    # Inicia Vazio
    ticker = st.text_input("INSIRA O TICKER PARA ANÁLISE (Ex: PETR4, BBAS3):", value="").upper()
    
    if ticker:
        # Busca Preço Automático
        try:
            stock_data = yf.Ticker(f"{ticker}.SA")
            preco_auto = stock_data.history(period="1d")['Close'].iloc[-1]
        except:
            preco_auto = 0.0

        with st.expander("📥 MÓDULO DE ENTRADA (PED)", expanded=True):
            txt = st.text_area("Área de Colagem (Investidor10):", key="ped_area")
            ext = garimpar_texto(txt) if txt else {}
            
            c_a, c_b, c_c = st.columns(3)
            val_p = c_a.number_input("Preço Atual (R$)", value=float(preco_auto if preco_auto > 0 else 10.0))
            val_lpa = c_a.number_input("1. LPA (R$)", value=float(ext.get('lpa', 0.0)))
            val_vpa = c_a.number_input("2. VPA (R$)", value=float(ext.get('vpa', 0.0)))
            val_dy = c_b.number_input("3. DY (%)", value=float(ext.get('dy', 0.0)))
            val_cagr = c_b.number_input("7. CAGR (%)", value=float(ext.get('cagr', 0.0)))
            val_roe = c_b.number_input("4. ROE (%)", value=float(ext.get('roe', 0.0)))
            val_setor = c_c.selectbox("8. Setor:", ["Bancos — Essencial Perene", "Energia — Essencial Perene", "Cíclico"])
            val_liq = c_c.number_input("6. Liquidez (R$/dia)", value=2000000.0)
            val_tend = c_c.selectbox("9. Tendência Lucros:", ["Crescente/Estável", "Decrescente"])

        if st.button("🚀 EXECUTAR ANÁLISE"):
            if val_lpa > 0 and val_vpa > 0:
                vi = math.sqrt(22.5 * val_lpa * val_vpa)
                margem = ((vi - val_p) / vi) * 100
                
                n_r = 20 if val_cagr > 10 else 10
                n_e = 20 if "Essencial" in val_setor else 10
                n_n = 20 if val_roe > 15 else 10
                n_a = 20 if margem > 20 else 10
                
                score = ((n_r + n_e + n_n + n_a) / 80) * 100
                j_real = selic - ipca

                relatorio = f"""
+----------------------------------------------------------------------+
| AVISO LEGAL -- O Metodo R.E.N.D.A. V.102.09 FULL                      |
+----------------------------------------------------------------------+
FASE 2: Scorecard Deterministico -- {ticker}

CALCULO DA MARGEM DE SEGURANCA (Pilar A)
- Resultado VI: R$ {vi:.2f}
- Margem: {margem:.2f}%

+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio            | Nota (0-20)| Diagnostico                      |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA            | {n_r:<10} | CAGR {val_cagr}%                       |
| E       | Setor               | {n_e:<10} | {val_setor[:30]} |
| N       | ROE                 | {n_n:<10} | ROE {val_roe}%                         |
| A (Ac.) | Graham              | {n_a:<10} | Margem {margem:.2f}% -- VI R${vi:.2f} |
+---------+---------------------+------------+----------------------------------+
| SCORE   | Base 100            | {score:.1f}/100    |                                  |
+---------+---------------------+------------+----------------------------------+

FASE 3: Diagnostico de Risco (Protocolo AVA)
- AVA-1 (Lucros): {'APROVADO' if val_tend != 'Decrescente' else 'VETO'}
- AVA-2 (Liquidez): {'APROVADO' if val_liq > 1000000 else 'VETO'}

Alerta Climatico: {'INVERNO' if j_real > 10 else 'VERAO'}. Juro Real: {j_real:.2f}%
SINTESE: Score {score:.1f}/100.
"""
                st.code(relatorio, language="text")
                
                # CORREÇÃO DEFINITIVA DO DOWNLOAD
                try:
                    pdf_data = gerar_pdf_bytes(relatorio)
                    st.download_button(
                        label="📥 Baixar Relatório em PDF",
                        data=pdf_data,
                        file_name=f"RENDA_{ticker}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

with aba2:
    st.subheader("🌲 MÓDULO C — VISÃO DO BOSQUE")
    txt_c = st.text_area("Cole aqui sua carteira:", key="c_area")
    ticks_f = re.findall(r'\b([A-Z]{4}[1-9]{1,2})\b', txt_c.upper()) if txt_c else []
    
    df_c = pd.DataFrame([{"Ticker": t, "Tipo": "Ações" if t[-1] in '34' else "FIIs", "Peso %": 10.0, "DY %": 8.0} for t in set(ticks_f)])
    if df_c.empty: df_c = pd.DataFrame([{"Ticker": "BBAS3", "Tipo": "Ações", "Peso %": 50.0, "DY %": 9.0}])
    
    edit_c = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)
    aporte = st.number_input("Aporte Mensal (R$):", value=1000.0)

    if st.button("⚖️ Executar"):
        dy_ponderado = (edit_c["DY %"] * (edit_c["Peso %"]/100)).sum()
        pat_alvo = (aporte * 12) / (dy_ponderado / 100) if dy_ponderado > 0 else 0
        st.success(f"💰 PATRIMÔNIO ALVO: R$ {pat_alvo:,.2f}")
        
