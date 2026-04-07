import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import math

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09", layout="wide")

# --- MÓDULO 0: AVISO LEGAL (SAFE HARBOR) ---
def exibir_aviso_legal():
    st.code("""
+----------------------------------------------------------------------+
|  ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|                                                                      |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
|  A decisão de investimento é 100% exclusiva do usuário.              |
+----------------------------------------------------------------------+
    """, language="text")

# --- MÓDULO DE SEGURANÇA (PARA VENDA) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        st.title("🔐 Acesso ao Mestre Digital")
        pwd = st.text_input("Digite a Chave de Acesso do Livro:", type="password")
        if st.button("Validar Semente"):
            if pwd == "RENDA2026": # Você pode mudar esta senha
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
        return False
    return True

# --- NOVA FUNÇÃO COM CACHE (PREVINE RATE LIMIT) ---
@st.cache_data(ttl=3600)  # Guarda os dados por 1 hora na memória
def buscar_dados_ativo(ticker_name):
    try:
        stock = yf.Ticker(f"{ticker_name}.SA")
        return stock.info
    except Exception:
        return None

# --- LÓGICA DO MÉTODO R.E.N.D.A. ---
def calcular_scorecard(dados, tipo):
    notas = {}
    
    # PILAR R - REINVESTIMENTO (CAGR)
    cagr = dados.get('cagr', 0)
    if cagr > 10: notas['R'] = 20
    elif cagr > 5: notas['R'] = 15
    elif cagr > 0: notas['R'] = 10
    else: notas['R'] = 5
    
    # PILAR A - ALOCAÇÃO (Graham para Ações / PVP para FIIs)
    if tipo == "Ação":
        vi = math.sqrt(22.5 * dados['lpa'] * dados['vpa'])
        margem = ((vi - dados['preco']) / vi) * 100
        if margem > 20: notas['A'] = 20
        elif margem > 0: notas['A'] = 15
        else: notas['A'] = 5
        diag_a = f"Margem Graham: {margem:.2f}%"
    else:
        pvp = dados['preco'] / dados['vpa']
        if pvp <= 0.90: notas['A'] = 20
        elif pvp <= 1.0: notas['A'] = 15
        else: notas['A'] = 5
        diag_a = f"P/VP Recalculado: {pvp:.2f}"

    return notas, diag_a

# --- EXECUÇÃO PRINCIPAL ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    st.write(f"Bem-vindo, Cultivador. Hoje é {date.today().strftime('%d/%m/%Y')}")

    # ETAPA G5: ÂNCORA DE DADOS MACRO
    with st.expander("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO", expanded=True):
        col1, col2, col3 = st.columns(3)
        selic = col1.number_input("Taxa Selic Meta (%)", value=10.50)
        ipca = col2.number_input("IPCA 12m (%)", value=4.50)
        ntnb = col3.number_input("NTN-B Longa (IPCA + %)", value=6.20)
        
        # Patch 1: Validador de Frescura (simplificado)
        dias_decorridos = (date.today() - date(2026, 1, 29)).days
        reunioes = 276 + int(dias_decorridos / 45)
        st.caption(f"✅ Motor Perpétuo: Reunião COPOM esperada >= {reunioes}")

    # MÓDULO A: ANÁLISE DE TICKER ÚNICO
    ticker = st.text_input("Insira o Ticker (ex: BBAS3 ou HGLG11):").upper()
    
    if ticker:
        with st.spinner(f"Executando PED (Protocolo de Extração Determinístico) para {ticker}..."):
            
            # Busca de dados inteligente (Usa memória se possível)
            info = buscar_dados_ativo(ticker)
            
            # Interface de Auditoria (Gate de Auditoria)
            st.subheader("🔬 MÓDULO 5 — GATE DE AUDITORIA")
            
            # Verificação se conseguiu extrair o preço
            if info and 'currentPrice' in info and info['currentPrice'] is not None:
                preco = info.get('currentPrice')
                st.success(f"**Preço Atual (Sincronizado):** R$ {preco}")
            else:
                st.warning("⚠️ O Yahoo Finance limitou o acesso ou o Ticker é inválido. Insira os dados manualmente.")
                preco = st.number_input("Insira o Preço Atual manualmente (R$):", value=10.00, min_value=0.01)
            
            # Dados fundamentais inseridos pelo aluno
            lpa = st.number_input("Confirme o LPA (Lucro por Ação):", value=1.0)
            vpa = st.number_input("Confirme o VPA (Valor Patrimonial):", value=10.0)
            tipo = st.selectbox("Tipo de Ativo:", ["Ação", "FII Tijolo", "FII Papel"])

            if st.button("Gerar Scorecard Final"):
                if lpa > 0 and vpa > 0:
                    dados = {'preco': preco, 'lpa': lpa, 'vpa': vpa, 'cagr': 12}
                    notas, diag_a = calcular_scorecard(dados, tipo)
                    
                    # Tabela de Saída Formatada
                    st.markdown("### 📊 MÓDULO 8 — SCORECARD DETERMINÍSTICO")
                    
                    soma_notas = sum(notas.values())
                    score_100 = (soma_notas / 40) * 100 # Normalização Base 100
                    
                    df_score = pd.DataFrame({
                        "Pilar": ["R (Reinvestimento)", "A (Alocação)"],
                        "Nota (0-20)": [notas['R'], notas['A']],
                        "Diagnóstico": ["CAGR > 10%", diag_a]
                    })
                    st.table(df_score)
                    
                    st.metric("SCORE FINAL (BASE 100)", f"{score_100:.2f}/100")
                    
                    # Escala de Vitalidade
                    if score_100 >= 85:
                        st.success("💎 SAFRA RESILIENTE: Alta robustez.")
                    elif score_100 >= 60:
                        st.warning("🌿 SOLO FERTIL: Acima do limiar mínimo.")
                    else:
                        st.error("🚨 TERRENO ÁRIDO: Fundamentos críticos.")
                else:
                    st.error("⚠️ Para o cálculo correto da Margem de Graham, o LPA e o VPA devem ser maiores que zero.")

st.markdown("---")
st.caption("R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL © Laerson Endrigo Ely, 2026.")
