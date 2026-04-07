import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import math
import re
from datetime import date

# --- CONFIGURAÇÃO DE ALTO NÍVEL ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", layout="wide")

def exibir_aviso_legal():
    st.code("""
+----------------------------------------------------------------------+
|  ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
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

def garimpar_dados_texto(texto):
    """Extrai fundamentos de texto bruto colado (Investidor10/StatusInvest)."""
    dados = {}
    def extrair(padrao, txt):
        m = re.search(padrao, txt, re.IGNORECASE)
        return float(m.group(1).replace('.', '').replace(',', '.')) if m else None
    
    dados['preco'] = extrair(r'(?:VALOR ATUAL|Cotação|Preço)[\s\S]{0,30}?R\$?\s*([0-9.,]+)', texto)
    dados['lpa'] = extrair(r'LPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['vpa'] = extrair(r'VPA[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['dy'] = extrair(r'(?:Dividend Yield|DY)[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['roe'] = extrair(r'ROE[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    dados['pvp'] = extrair(r'P/VP[\s\S]{0,20}?([0-9.,]+)', texto)
    dados['cagr'] = extrair(r'CAGR\s+LUCROS[\s\S]{0,20}?([0-9.,]+)\s*%', texto)
    return dados

# --- LÓGICA DO SCORECARD ---
def calcular_scorecard(p, tipo, macro):
    notas = {}
    alertas = []
    
    # R - REINVESTIMENTO (CAGR)
    notas['R'] = 20 if p['cagr'] > 10 else 15 if p['cagr'] > 5 else 10 if p['cagr'] > 0 else 5
    
    # E - ESSENCIAIS
    notas['E'] = 20 if p['setor'] == "Essencial Perene" else 15 if p['setor'] == "Essencial Moderado" else 5
    
    # N - NEGÓCIOS SÓLIDOS & AVA
    if tipo == "AÇÃO":
        notas['N'] = 20 if p['roe'] > 18 else 15 if p['roe'] >= 12 else 10 if p['roe'] >= 7 else 5
        if p['div_ebitda'] > 4.0: alertas.append("🚨 AVA-2: Risco de Ruína (Dívida/EBITDA > 4.0)")
        if p['tendencia'] == "Decrescente": alertas.append("🚨 AVA-1: Destruição de Valor (Lucros em Queda)")
    else: # FIIs
        notas['N'] = 20 if p['vacancia'] < 5 else 15 if p['vacancia'] <= 10 else 5
        if p['ltv'] > 25: alertas.append("🚨 AVA-2: Alavancagem Excessiva (LTV > 25%)")

    # A - ALOCAÇÃO
    if tipo == "AÇÃO":
        vi = math.sqrt(22.5 * p['lpa'] * p['vpa']) if p['lpa'] > 0 else 0
        margem = ((vi - p['preco']) / vi) * 100 if vi > 0 else -100
        notas['A'] = 20 if margem > 20 else 15 if margem > 0 else 10 if margem > -20 else 5
        diag_a = f"Margem Graham: {margem:.1f}% (VI: R$ {vi:.2f})"
    else:
        pvp = p['preco'] / p['vpa'] if p['vpa'] > 0 else 1
        notas['A'] = 20 if pvp < 0.95 else 15 if pvp <= 1.05 else 5
        diag_a = f"P/VP: {pvp:.2f}"
    
    return notas, alertas, diag_a

# --- INÍCIO DA INTERFACE ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    
    # 🌐 G5 - MACRO
    selic_a, ipca_a = buscar_dados_macro()
    with st.expander("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO", expanded=True):
        c1, c2, c3 = st.columns(3)
        selic = c1.number_input("Selic Meta (%)", value=selic_auto if 'selic_auto' in locals() else selic_a)
        ipca = c2.number_input("IPCA 12m (%)", value=ipca_auto if 'ipca_auto' in locals() else ipca_a)
        ntnb = c3.number_input("NTN-B Longa (IPCA + %)", value=6.20)

    tab_a, tab_c = st.tabs(["🌳 Módulo A: Ativo Único", "🌲 Módulo C: Visão do Bosque (Carteira)"])

    # =====================================================================
    # MÓDULO A: ANÁLISE COMPLETA
    # =====================================================================
    with tab_a:
        st.subheader("🔬 PROTOCOLO DE EXTRAÇÃO DETERMINÍSTICO (PED)")
        
        # Sincronização Inteligente
        col_t, col_s = st.columns([1, 2])
        ticker = col_t.text_input("Ticker (ex: BBAS3, HGLG11):").upper()
        
        with st.expander("📥 Garimpo Automático (Copiar/Colar Página Inteira)"):
            texto_página = st.text_area("Aperte CTRL+A e CTRL+C na página do ativo e cole aqui:")
            extraidos = garimpar_dados_texto(texto_página) if texto_página else {}
            if extraidos: st.success("✅ Inteligência do Mestre: Dados extraídos do texto!")

        tipo = st.radio("Natureza do Ativo:", ["AÇÃO", "FII TIJOLO", "FII PAPEL"], horizontal=True)

        st.markdown("---")
        # Os 9 Campos do PED (Auditoria)
        cA, cB, cC = st.columns(3)
        with cA:
            p_atual = st.number_input("Preço Atual (R$)", value=extraidos.get('preco', 10.0))
            f1 = st.number_input("1. LPA (R$)" if tipo == "AÇÃO" else "1. Vacância (%)", value=extraidos.get('lpa', 1.0) if tipo == "AÇÃO" else 5.0)
            f2 = st.number_input("2. VPA (R$)", value=extraidos.get('vpa', 10.0))
        with cB:
            f3 = st.number_input("3. DY 12m (%)", value=extraidos.get('dy', 6.0))
            f4 = st.number_input("4. ROE (%)" if tipo == "AÇÃO" else "4. Nota de Gestão (0-20)", value=extraidos.get('roe', 15.0))
            f5 = st.number_input("5. Dívida/EBITDA" if tipo == "AÇÃO" else "5. LTV/Alavancagem (%)", value=1.5 if tipo == "AÇÃO" else 10.0)
        with cC:
            f6 = st.number_input("6. Liquidez Diária (R$ Milhões)", value=5.0)
            f7 = st.number_input("7. CAGR Proventos 3a (%)", value=extraidos.get('cagr', 8.0))
            f9_setor = st.selectbox("8/9. Setor/Essencialidade:", ["Essencial Perene", "Essencial Moderado", "Cíclico"])
            f9_tend = st.selectbox("9. Tendência de Lucros:", ["Crescente/Estável", "Decrescente"])

        if st.button("📊 EXECUTAR ANÁLISE R.E.N.D.A."):
            params = {
                'preco': p_atual, 'lpa': f1, 'vpa': f2, 'dy': f3, 'roe': f4, 
                'div_ebitda': f5, 'cagr': f7, 'setor': f9_setor, 'tendencia': f9_tend,
                'vacancia': f1, 'ltv': f5 # Para FIIs
            }
            notas, alertas, diag_a = calcular_scorecard(params, tipo, (selic, ipca))
            
            st.markdown(f"### 📊 Scorecard V.102.09: {ticker}")
            df_res = pd.DataFrame({
                "Pilar": ["R (Reinvestimento)", "E (Essenciais)", "N (Negócios)", "D (Diversificação)", "A (Alocação)"],
                "Nota (0-20)": [notas['R'], notas['E'], notas['N'], "---", notas['A']],
                "Diagnóstico": [f"CAGR {f7}%", f9_setor, "Análise de Fundamentos", "Validado no Módulo C", diag_a]
            })
            st.table(df_res)
            
            score_100 = (sum(notas.values()) / 80) * 100
            st.metric("🎯 SCORE FINAL (BASE 100)", f"{score_100:.1f} pts")

            # ESCALA DE VITALIDADE
            st.markdown("#### 🧬 Escala de Vitalidade do Solo")
            if score_100 >= 85: st.success("💎 SAFRA RESILIENTE: Solo de altíssima fertilidade. (Acima do limiar)")
            elif score_100 >= 60: st.warning("🌿 SOLO FÉRTIL: Base sólida, mas exige monitoramento AVA-3.")
            else: st.error("🚨 TERRENO ÁRIDO: Fundamentos críticos. Risco de ruína detectado.")

            for a in alertas: st.error(a)

    # =====================================================================
    # MÓDULO C: VISÃO DO BOSQUE
    # =====================================================================
    with tab_c:
        st.subheader("🌲 MÓDULO C — ANÁLISE DA CARTEIRA")
        st.info("Regra do Talmud: 1/3 Ações | 1/3 FIIs | 1/3 Renda Fixa")
        
        with st.expander("📥 Importar da Corretora (Copiar/Colar)"):
            txt_c = st.text_area("Cole aqui a lista de ativos da sua corretora/consolidador:")
            ticks_encontrados = re.findall(r'\b([A-Z]{4}[1-9]{1,2})\b', txt_c.upper())
            if ticks_encontrados: st.success(f"Ativos detectados: {', '.join(set(ticks_encontrados))}")

        # Tabela de Carteira
        base_cart = pd.DataFrame([{"Ticker": t, "Tipo": "Ações" if t[-1] in '34' else "FIIs", "% Carteira": 10.0, "DY %": 8.0} for t in set(ticks_encontrados)])
        if base_cart.empty: base_cart = pd.DataFrame([{"Ticker": "EXEMPLO", "Tipo": "Ações", "% Carteira": 100.0, "DY %": 8.0}])
        
        edit_cart = st.data_editor(base_cart, num_rows="dynamic", use_container_width=True)
        aporte_m = st.number_input("Seu Aporte Mensal Médio (R$)", value=1000.0)

        if st.button("⚖️ VALIDAR EQUILÍBRIO DO BOSQUE"):
            perc_a = edit_cart[edit_cart["Tipo"] == "Ações"]["% Carteira"].sum()
            perc_f = edit_cart[edit_cart["Tipo"] == "FIIs"]["% Carteira"].sum()
            perc_rf = 100 - perc_a - perc_f
            
            st.markdown("#### C.1 Termômetro do Talmud")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ações", f"{perc_a:.1f}%", f"{33.3-perc_a:.1f}% do Alvo")
            c2.metric("FIIs", f"{perc_f:.1f}%", f"{33.3-perc_f:.1f}% do Alvo")
            c3.metric("Renda Fixa", f"{perc_rf:.1f}%", f"{33.3-perc_rf:.1f}% do Alvo")
            
            # SIMULADOR GRANDE VIRADA
            dy_ponderado = (edit_cart["DY %"] * (edit_cart["% Carteira"]/100)).sum()
            patrimonio_virada = (aporte_m * 12) / (dy_ponderado / 100) if dy_ponderado > 0 else 0
            
            st.markdown("#### 🌱 C.3 Simulador da Grande Virada")
            st.write(f"Para que seus proventos mensais igualem seu aporte de **R$ {aporte_m:.2f}**, seu alvo é:")
            st.success(f"💰 PATRIMÔNIO ALVO: R$ {patrimonio_virada:,.2f}")
            st.caption(f"Com um Dividend Yield Médio de {dy_ponderado:.2f}% ao ano.")
