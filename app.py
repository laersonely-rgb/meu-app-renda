import streamlit as st
import pandas as pd
import requests
import math
import re
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def exibir_aviso_legal():
    st.code("""
+----------------------------------------------------------------------+
|  ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
|  A decisão de investimento é 100% exclusiva do usuário.              |
+----------------------------------------------------------------------+
    """, language="text")

def check_password():
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
        return False
    return True

# --- 🤖 MOTOR DE INTELIGÊNCIA MACRO E EXTRAÇÃO ---
@st.cache_data(ttl=3600)
def buscar_dados_macro():
    try:
        selic = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1").json()[0]['valor'])
        ipca = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1").json()[0]['valor'])
        return selic, ipca
    except:
        return 10.50, 4.50

def garimpar_dados(texto):
    dados = {}
    def extrair(padrao, txt):
        m = re.search(padrao, txt, re.IGNORECASE)
        return float(m.group(1).replace('.', '').replace(',', '.')) if m else None
    
    dados['preco'] = extrair(r'(?:VALOR ATUAL|Cotação|Preço)[\s\S]{0,30}?R\$?\s*([0-9.,]+)', texto)
    dados['lpa'] = extrair(r'LPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['vpa'] = extrair(r'VPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['dy'] = extrair(r'(?:Dividend Yield|DY)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['roe'] = extrair(r'ROE[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['cagr'] = extrair(r'(?:CAGR LUCROS|CAGR RECEITA)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    return dados

# --- EXECUÇÃO DO SISTEMA ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    st.caption("Protocolo V.102.09 FULL — O Mestre Digital")

    # 🌐 ETAPA G5 — ÂNCORA MACRO
    with st.expander("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO", expanded=True):
        s_auto, i_auto = buscar_dados_macro()
        c1, c2, c3 = st.columns(3)
        selic = c1.number_input("Taxa Selic Meta (%)", value=s_auto)
        ipca = c2.number_input("IPCA 12m (%)", value=i_auto)
        ntnb = c3.number_input("NTN-B Longa (IPCA + %)", value=6.20)
        st.info(f"**Juro Real Bruto:** {selic - ipca:.2f}%")

    tab_a, tab_c = st.tabs(["🌳 Módulo A: Ativo Único (PED/AVA)", "🌲 Módulo C: Visão do Bosque (Carteira)"])

    # =====================================================================
    # MÓDULO A: ANÁLISE DETERMINÍSTICA
    # =====================================================================
    with tab_a:
        st.subheader("🔬 PROTOCOLO DE EXTRAÇÃO DETERMINÍSTICO (PED)")
        
        with st.expander("📥 GARIMPO AUTOMÁTICO (CTRL+A / CTRL+V)"):
            texto_i10 = st.text_area("Cole aqui o texto da página do ativo no Investidor10/StatusInvest:")
            extraidos = garimpar_dados(texto_i10) if texto_i10 else {}
            if extraidos: st.success("✅ Dados garimpados com sucesso!")

        ticker = st.text_input("Ticker do Ativo:").upper()
        tipo = st.radio("Natureza:", ["AÇÃO", "FII TIJOLO", "FII PAPEL"], horizontal=True)

        st.markdown("#### Auditoria dos 9 Campos do PED")
        col1, col2, col3 = st.columns(3)
        with col1:
            preco_at = col1.number_input("Preço Atual (R$)", value=extraidos.get('preco', 10.0))
            f1 = col1.number_input("1. LPA (R$)" if tipo == "AÇÃO" else "1. Vacância (%)", value=extraidos.get('lpa', 1.0) if tipo == "AÇÃO" else 5.0)
            f2 = col1.number_input("2. VPA (R$)", value=extraidos.get('vpa', 10.0))
        with col2:
            f3 = col2.number_input("3. DY 12m (%)", value=extraidos.get('dy', 6.0))
            f4 = col2.number_input("4. ROE (%)" if tipo == "AÇÃO" else "4. Gestão (Nota 0-20)", value=extraidos.get('roe', 15.0) if tipo == "AÇÃO" else 18.0)
            f5 = col2.number_input("5. Dívida/EBITDA" if tipo == "AÇÃO" else "5. LTV/Alavancagem (%)", value=1.5 if tipo == "AÇÃO" else 10.0)
        with col3:
            f6 = col3.number_input("6. Liquidez Diária (R$ Milhões)", value=5.0)
            f7 = col3.number_input("7. CAGR Proventos 3a (%)", value=extraidos.get('cagr', 8.0))
            f9 = col3.selectbox("9. Tendência/Setor", ["Essencial Perene", "Essencial Moderado", "Cíclico", "Ruim/Decrescente"])

        if st.button("📊 Gerar Scorecard R.E.N.D.A."):
            notas = {}
            alertas = []
            
            # PILAR R (Reinvestimento)
            notas['R'] = 20 if f7 > 10 else 15 if f7 > 5 else 10 if f7 > 0 else 5
            
            # PILAR E (Essenciais)
            notas['E'] = 20 if "Perene" in f9 else 15 if "Moderado" in f9 else 5
            
            # PILAR N (Negócios) + AVA
            if tipo == "AÇÃO":
                notas['N'] = 20 if f4 > 20 else 15 if f4 > 12 else 5
                if f5 > 4.0: alertas.append("🚨 AVA-2: Risco de Ruína (Dívida alta)")
                if "Ruim" in f9: alertas.append("🚨 AVA-1: Destruição de Valor")
            else:
                notas['N'] = 20 if f1 < 5 else 10 # Para FII, f1 é vacância
            
            # PILAR A (Alocação)
            if tipo == "AÇÃO":
                margem = (math.sqrt(22.5 * f1 * f2) - preco_at) / math.sqrt(22.5 * f1 * f2) * 100 if f1 > 0 else -100
                notas['A'] = 20 if margem > 20 else 15 if margem > 0 else 5
                diag_a = f"Margem Graham: {margem:.1f}%"
            else:
                pvp = preco_at / f2
                notas['A'] = 20 if pvp < 0.95 else 15 if pvp <= 1.05 else 5
                diag_a = f"P/VP: {pvp:.2f}"

            # EXIBIÇÃO DO SCORECARD
            st.markdown(f"### Scorecard Deterministico: {ticker}")
            df_renda = pd.DataFrame({
                "Pilar": ["R (Reinvestimento)", "E (Essenciais)", "N (Negócios Sólidos)", "D (Diversificação)", "A (Alocação)"],
                "Nota (0-20)": [notas['R'], notas['E'], notas['N'], "---", notas['A']],
                "Diagnóstico": [f"CAGR {f7}%", f9, "Fundamentos", "Ver Módulo C", diag_a]
            })
            st.table(df_renda)
            
            score = (sum(notas.values()) / 80) * 100
            st.metric("SCORE FINAL (BASE 100)", f"{score:.1f} pts")
            
            # ESCALA DE VITALIDADE
            st.markdown("#### 🧬 Escala de Vitalidade do Solo")
            if score >= 85: st.success("💎 SAFRA RESILIENTE: Solo fértil, alta robustez.")
            elif score >= 60: st.warning("🌿 SOLO MODERADO: Exige monitoramento AVA-3.")
            else: st.error("🚨 TERRENO ÁRIDO: Risco de ruína detectado.")

            for a in alertas: st.error(a)

    # =====================================================================
    # MÓDULO C: VISÃO DO BOSQUE
    # =====================================================================
    with tab_c:
        st.subheader("🌲 MÓDULO C — VISÃO DO BOSQUE")
        st.write("Importe sua carteira para validar a **Regra do Talmud (1/3)**.")
        
        with st.expander("📥 Importar de Consolidador"):
            txt_cart = st.text_area("Cole aqui sua lista de ativos/corretora:")
            # Garimpo simplificado de tickers
            ticks_f = re.findall(r'\b([A-Z]{4}[1-9]{1,2})\b', txt_cart.upper()) if txt_cart else []
            if ticks_f: st.success(f"Encontrados: {', '.join(set(ticks_f))}")

        # Tabela de Carteira
        cart_data = pd.DataFrame([{"Ticker": t, "Tipo": "Ações" if t[-1] in '34' else "FIIs", "Peso %": 10.0, "DY %": 8.0} for t in set(ticks_f)])
        if cart_data.empty: cart_data = pd.DataFrame([{"Ticker": "EXEMPLO", "Tipo": "Ações", "Peso %": 100.0, "DY %": 8.0}])
        
        edit_df = st.data_editor(cart_data, num_rows="dynamic", use_container_width=True)
        aporte = st.number_input("Aporte Mensal (R$)", value=1000.0)

        if st.button("⚖️ Executar Equilíbrio do Talmud"):
            acoes = edit_df[edit_df["Tipo"]=="Ações"]["Peso %"].sum()
            fiis = edit_df[edit_df["Tipo"]=="FIIs"]["Peso %"].sum()
            rf = 100 - acoes - fiis
            
            st.markdown("#### C.1 Termômetro do Talmud")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ações (Alvo 33%)", f"{acoes}%")
            c2.metric("FIIs (Alvo 33%)", f"{fiis}%")
            c3.metric("Renda Fixa (Alvo 33%)", f"{rf}%")
            
            # SIMULADOR GRANDE VIRADA
            dy_m = (edit_df["DY %"] * (edit_df["Peso %"]/100)).sum()
            pat_v = (aporte * 12) / (dy_m / 100) if dy_m > 0 else 0
            
            st.markdown("#### 🌱 C.3 Simulador da Grande Virada")
            st.write(f"Para que seus dividendos igualem seu aporte de **R$ {aporte:.2f}**, seu alvo é:")
            st.success(f"💰 PATRIMÔNIO ALVO: R$ {pat_v:,.2f}")
