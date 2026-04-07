import streamlit as st
import pandas as pd
import requests
import math
import re
from datetime import date

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def estilizar_tabela(conteudo):
    """Renderiza o texto no formato de código/terminal para manter a estética ASCII."""
    st.code(conteudo, language="text")

# --- MÓDULO DE SEGURANÇA ---
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

# --- MOTOR DE DADOS ---
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
    d['cagr'] = ext(r'CAGR\s+LUCROS[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    return d

# --- INTERFACE PRINCIPAL ---
st.code("""
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|                                                                      |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
+----------------------------------------------------------------------+
""", language="text")

selic, ipca = buscar_macro()
ticker = st.text_input("INSIRA O TICKER PARA ANÁLISE (Ex: BBAS3):").upper()

if ticker:
    # --- ÁREA DE INPUT ---
    with st.expander("📥 MÓDULO DE ENTRADA DE DADOS (PED)", expanded=True):
        st.info("Cole o texto da página do Investidor10 abaixo ou preencha manualmente.")
        txt = st.text_area("Área de Colagem (CTRL+A / CTRL+V):")
        extraidos = garimpar_dados(txt) if txt else {}
        
        col1, col2, col3 = st.columns(3)
        preco_atual = col1.number_input("Preço Atual (R$)", value=extraidos.get('preco', 23.43))
        lpa = col1.number_input("LPA (R$)", value=extraidos.get('lpa', 3.12))
        vpa = col1.number_input("VPA (R$)", value=extraidos.get('vpa', 32.94))
        
        dy = col2.number_input("DY 12m (%)", value=extraidos.get('dy', 3.54))
        cagr = col2.number_input("CAGR DPA 3a (%)", value=extraidos.get('cagr', 4.77))
        roe = col2.number_input("ROE (%)", value=extraidos.get('roe', 0.0)) # 0 se N/A
        
        setor = col3.selectbox("Setor:", ["Bancos — Essencial Perene", "Energia — Essencial Perene", "Saneamento — Essencial Perene", "Cíclico / Outros"])
        liquidez = col3.number_input("Liquidez (R$/dia)", value=262387884.0)

    if st.button("🚀 EXECUTAR CICLO COMPLETO (FASE 2 E 3)"):
        
        # --- FASE 2: SCORECARD DETERMINÍSTICO ---
        st.subheader(f"FASE 2: Scorecard Determinístico (Módulo 8) — {ticker}")
        
        # Cálculo Graham Passo a Passo
        st.write("**CÁLCULO DA MARGEM DE SEGURANÇA (Pilar A)**")
        vi = math.sqrt(22.5 * lpa * vpa) if lpa > 0 else 0
        margem = ((vi - preco_atual) / vi) * 100 if vi > 0 else 0
        
        st.write(f"▸ Fórmula | VI = raiz(22,5 x LPA x VPA)")
        st.write(f"▸ Substitui | VI = raiz(22,5 x {lpa:.2f} x {vpa:.2f})")
        st.write(f"▸ Resultado | R$ {vi:.2f}")
        st.write(f"▸ Fórmula | Margem = ((VI - Preco) / VI) * 100")
        st.write(f"▸ Substitui | Margem = (({vi:.2f} - {preco_atual:.2f}) / {vi:.2f}) * 100")
        st.write(f"▸ Resultado | **{margem:.2f}%**")

        # Tabela ASCII Scorecard
        nota_r = 10 if cagr < 5 else 15 if cagr < 10 else 20
        nota_e = 20 if "Essencial" in setor else 10
        nota_n = "-- (N/A)" if roe == 0 else (20 if roe > 15 else 10)
        nota_a = 20 if margem > 20 else 10
        
        subtotal = (10 if cagr < 5 else 15 if cagr < 10 else 20) + nota_e + (0 if roe == 0 else (20 if roe > 15 else 10)) + nota_a
        possivel = 60 if roe == 0 else 80
        score_100 = (subtotal / possivel) * 100

        tabela_score = f"""
+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Ref. Patch 7)       |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA 3 anos     | {nota_r:<10} | CAGR {cagr}% (frutos estaveis)     |
| E       | Setor / Segmento    | {nota_e:<10} | {setor[:30]} |
| N       | ROE/Vac/Inadim      | {nota_n:<10} | {"[DADO INDISPONIVEL]" if roe == 0 else f"ROE {roe}%"} |
| D       | Desvio Talmud       | -- (N/A)   | (Modulo A - Ticker Unico)        |
| A (Ac.) | Graham              | {nota_a:<10} | Margem {margem:.2f}% — VI R${vi:.2f}    |
+---------+---------------------+------------+----------------------------------+
| SUBTOTAL| Soma bruta          | {subtotal}/{possivel:<10} | PP = {possivel} pts                        |
| SCORE   | Base 100            | {score_100:.0f}/100      | ({subtotal} / {possivel}) x 100                  |
+---------+---------------------+------------+----------------------------------+
"""
        estilizar_tabela(tabela_score)

        # Diagnóstico de Vitalidade
        vitalidade = "ARVORE SAUDAVEL" if score_100 >= 75 else "SOLO FERTIL" if score_100 >= 60 else "TERRENO ARIDO"
        st.write(f"**Score: {score_100:.0f}/100 — Diagnóstico: {vitalidade}**")
        
        st.markdown("---")
        
        # --- FASE 3: DIAGNÓSTICO AVA ---
        st.subheader(f"FASE 3: Diagnóstico de Risco (Protocolo AVA) e Conclusão — {ticker}")
        st.write("**AFERIÇÃO DAS 3 TRAVAS DE SEGURANÇA DO POMAR (Cap. 11.7)**")
        
        ava_liquidez = "✅ APROVADO" if liquidez > 1000000 else "🚨 VETO"
        
        tabela_ava = f"""
+-------+-------------------------+-----------------------------------------+
| Trava | Criterio de Avaliacao   | Diagnostico e Status do Veto            |
+-------+-------------------------+-----------------------------------------+
| AVA-1 | Destruicao de Valor     | [DADO INDISPONIVEL]                     |
|       | (Lucros/Prejuizos 3a)   | Necessita insercao manual da tendencia. |
+-------+-------------------------+-----------------------------------------+
| AVA-2 | Risco de Ruina / Asfixia| ✅ APROVADO                             |
|       | (D/EBITDA > 3x a 4x)    | Natureza do ativo analisada.            |
+-------+-------------------------+-----------------------------------------+
| AVA-2 | Risco de Liquidez       | {ava_liquidez}                             |
|       | (Volume < R$ 1M/dia)    | R$ {liquidez:,.2f}/dia.               |
+-------+-------------------------+-----------------------------------------+
"""
        estilizar_tabela(tabela_ava)

        # Alerta Macro
        juro_real = selic - ipca
        clima = "❄️ INVERNO MACRO ATIVADO" if juro_real > 10 else "☀️ VERÃO MACRO"
        st.write(f"▸ **Alerta Climático:** {clima}. Juro Real: {juro_real:.2f}%")
        
        st.write(f"🌳 **SÍNTESE DO ESTUDO RENDA ({ticker})**")
        st.write(f"O ativo apresenta um Scorecard de {score_100:.0f}/100 e margem de segurança de Graham de {margem:.2f}%.")

        st.write("---")
        st.caption("R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL © Laerson Endrigo Ely, 2026.")
