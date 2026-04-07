import streamlit as st
import pandas as pd
import math
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09", layout="wide")

def exibir_aviso_legal():
    st.code("""
+----------------------------------------------------------------------+
|  ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|  Exercício estritamente educacional e matemático.                    |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
+----------------------------------------------------------------------+
    """, language="text")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.title("🔐 Acesso ao Mestre Digital")
        pwd = st.text_input("Chave de Acesso:", type="password")
        if st.button("Validar Semente"):
            if pwd == "RENDA2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
        return False
    return True

# --- EXECUÇÃO PRINCIPAL ---
exibir_aviso_legal()

if check_password():
    st.title("🌱 Sistema de Ensino R.E.N.D.A.")
    
    # 🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO
    with st.expander("🌐 ETAPA G5 — ÂNCORA DE DADOS MACRO", expanded=True):
        c1, c2, c3 = st.columns(3)
        selic = c1.number_input("Selic Meta (%)", value=10.50)
        ipca = c2.number_input("IPCA 12m (%)", value=4.50)
        ntnb = c3.number_input("NTN-B Longa (IPCA + %)", value=6.20)
        juro_real = selic - ipca
        st.info(f"**Juro Real (Selic - IPCA):** {juro_real:.2f}% " + ("❄️ INVERNO MACRO (Atenção aos FIIs)" if juro_real > 10 else "☀️ VERÃO MACRO"))

    # --- SISTEMA DE ABAS (TABS) ---
    aba_a, aba_c = st.tabs(["🌳 Módulo A: Análise Individual", "🌲 Módulo C: Visão do Bosque (Carteira)"])

    # =====================================================================
    # ABA 1: MÓDULO A (ATIVO ÚNICO E PROTOCOLOS AVA)
    # =====================================================================
    with aba_a:
        st.subheader("🔬 PROTOCOLO DE EXTRAÇÃO DETERMINÍSTICO (PED)")
        ticker = st.text_input("Ticker do Ativo:").upper()
        tipo_ativo = st.radio("Natureza do Ativo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"], horizontal=True)

        if ticker:
            st.markdown("Preencha os **9 Campos Obrigatórios** (Extraia do Investidor10 / StatusInvest):")
            cA, cB, cC = st.columns(3)
            
            with cA:
                preco = st.number_input("Preço Atual (R$)", value=10.0)
                lpa = st.number_input("Campo 1: LPA (R$)", value=1.0) if tipo_ativo == "AÇÕES" else 0
                vpa = st.number_input("Campo 2: VPA (R$)", value=10.0)
                dy = st.number_input("Campo 3: DY 12m (%)", value=6.0)
            
            with cB:
                cagr = st.number_input("Campo 7: CAGR Div. 3 anos (%)", value=5.0)
                liquidez = st.number_input("Campo 6: Liquidez Diária (R$ Milhões)", value=5.0)
                
                if tipo_ativo == "AÇÕES":
                    roe = st.number_input("Campo 4: ROE (%)", value=15.0)
                    div_ebitda = st.number_input("Campo 5: Dívida Líq / EBITDA", value=1.5)
                elif tipo_ativo == "FII TIJOLO":
                    vacancia = st.number_input("Campo 9A: Vacância (%)", value=4.0)
                    ltv = st.number_input("Campo 5: LTV (%)", value=15.0)
                elif tipo_ativo == "FII PAPEL":
                    inadimplencia = st.number_input("Campo 9B: Inadimplência (%)", value=0.5)

            with cC:
                if tipo_ativo == "AÇÕES":
                    setor = st.selectbox("Pilar E - Setor:", ["Essencial Perene", "Essencial Moderado", "Semi-Essencial", "Cíclico"])
                    tendencia = st.selectbox("Campo 9C: Tendência Lucros:", ["Crescente", "Estável", "Decrescente 3 anos", "Prejuízo Recorrente"])
                elif tipo_ativo == "FII TIJOLO":
                    setor = st.selectbox("Pilar E - Segmento:", ["Tijolo Essencial", "Tijolo Misto", "Tijolo Cíclico"])
                elif tipo_ativo == "FII PAPEL":
                    setor = st.selectbox("Pilar E - Lastro:", ["CRI Setores Essenciais", "CRI Diversificado"])

            if st.button("Executar Scorecard R.E.N.D.A."):
                notas = {}
                diag = {}
                alertas_ava = []
                pequena_cap = False

                # Pilar R: Reinvestimento
                if cagr > 10: notas['R'] = 20
                elif cagr > 5: notas['R'] = 15
                elif cagr > 0: notas['R'] = 10
                else: notas['R'] = 5
                diag['R'] = f"CAGR: {cagr}%"

                # Pilar E: Essenciais
                notas['E'] = 20 if "Essencial" in setor and "Semi" not in setor else 15 if "Moderado" in setor or "Misto" in setor else 10 if "CRI Diversificado" in setor or "Semi" in setor else 5
                diag['E'] = setor

                # Pilar N: Negócios Sólidos & AVA-1/AVA-2
                if tipo_ativo == "AÇÕES":
                    notas['N'] = 20 if roe > 20 else 15 if roe >= 15 else 10 if roe >= 10 else 5
                    diag['N'] = f"ROE: {roe}%"
                    
                    if liquidez < 0.5 and div_ebitda < 1.5 and cagr > 5 and tendencia in ["Crescente", "Estável"]:
                        pequena_cap = True
                        diag['N'] += " (Contexto Small Cap)"

                    if div_ebitda > 4.0: alertas_ava.append("🚨 AVA-2 RISCO DE RUÍNA: Dívida/EBITDA > 4x.")
                    if tendencia in ["Decrescente 3 anos", "Prejuízo Recorrente"]: alertas_ava.append("🚨 AVA-1: Destruição de Valor (Lucros decrescentes/prejuízo).")

                elif tipo_ativo == "FII TIJOLO":
                    notas['N'] = 20 if vacancia < 5 else 15 if vacancia <= 10 else 10 if vacancia <= 15 else 5
                    diag['N'] = f"Vacância: {vacancia}%"
                    if ltv > 25: alertas_ava.append("🚨 AVA-2 RISCO DE RUÍNA: LTV > 25%.")

                elif tipo_ativo == "FII PAPEL":
                    notas['N'] = 20 if inadimplencia < 1 else 15 if inadimplencia <= 3 else 10 if inadimplencia <= 5 else 5
                    diag['N'] = f"Inadimplência: {inadimplencia}%"

                # Pilar A: Alocação
                if tipo_ativo == "AÇÕES":
                    if lpa > 0 and vpa > 0:
                        vi = math.sqrt(22.5 * lpa * vpa)
                        margem = ((vi - preco) / vi) * 100
                        notas['A'] = 20 if margem > 20 else 15 if margem > 0 else 10 if margem >= -20 else 5
                        diag['A'] = f"Margem: {margem:.1f}% (VI: R${vi:.2f})"
                    else:
                        notas['A'] = 5
                        diag['A'] = "Graham Inválido"
                elif tipo_ativo == "FII TIJOLO":
                    pvp = preco / vpa if vpa > 0 else 999
                    notas['A'] = 20 if pvp <= 0.90 else 15 if pvp <= 1.0 else 10 if pvp <= 1.10 else 5
                    diag['A'] = f"P/VP: {pvp:.2f}"
                elif tipo_ativo == "FII PAPEL":
                    spread = dy - ntnb
                    notas['A'] = 20 if spread > 4.0 else 15 if spread >= 2.0 else 10 if spread > 0 else 5
                    diag['A'] = f"Spread: {spread:.2f} p.p."

                if liquidez < 1.0: alertas_ava.append("🚨 AVA-2 RISCO DE LIQUIDEZ: < R$ 1M/dia.")

                # Tabela Módulo 8
                st.markdown(f"### 📊 MÓDULO 8 — SCORECARD DETERMINÍSTICO ({ticker})")
                df_score = pd.DataFrame({
                    "Pilar": ["R (Reinvestimento)", "E (Essenciais)", "N (Negócios Sólidos)", "D (Diversificação)", "A (Alocação)"],
                    "Nota (0-20)": [notas['R'], notas['E'], notas['N'], "-- (N/A)", notas['A']],
                    "Diagnóstico": [diag['R'], diag['E'], diag['N'], "(Módulo C)", diag['A']]
                })
                st.table(df_score)

                # Cálculo Normalizado
                score_100 = (sum(notas.values()) / 80) * 100
                st.metric("🎯 SCORE FINAL (BASE 100)", f"{score_100:.1f} / 100")

                if pequena_cap:
                    st.info("⚠️ CONTEXTO SMALL CAP: ROE pode refletir fase de reinvestimento acelerado e não ineficiência.")

                if alertas_ava:
                    st.error("### ⚠️ TRAVAS DE SEGURANÇA ATIVADAS")
                    for a in alertas_ava: st.write(a)

                # Escala de Vitalidade
                if score_100 >= 85: st.success("💎 SAFRA RESILIENTE: Alta robustez.")
                elif score_100 >= 75: st.info("🌳 ÁRVORE SAUDÁVEL: Fundamentos sólidos.")
                elif score_100 >= 60: st.warning("🌿 SOLO FÉRTIL: Acima do limiar mínimo.")
                else: st.error("☠️ TERRENO ÁRIDO: Fundamentos críticos.")

    # =====================================================================
    # ABA 2: MÓDULO C (VISÃO DO BOSQUE / CARTEIRA)
    # =====================================================================
    with aba_c:
        st.subheader("🌳 MÓDULO C — ANÁLISE DE CARTEIRA (VISÃO DO BOSQUE)")
        st.write("Insira os ativos da sua carteira para calcularmos o **Pilar D (Diversificação)** e a **Grande Virada**.")
        
        # Tabela interativa para o aluno preencher
        dados_iniciais = pd.DataFrame([
            {"Ticker": "BBAS3", "% Cart": 30.0, "Tipo": "AÇÕES", "DY (%)": 8.5},
            {"Ticker": "HGLG11", "% Cart": 40.0, "Tipo": "FIIs", "DY (%)": 9.0},
            {"Ticker": "TESOURO", "% Cart": 30.0, "Tipo": "RENDA FIXA", "DY (%)": 10.5}
        ])
        
        cart_df = st.data_editor(dados_iniciais, num_rows="dynamic", use_container_width=True)

        col1_c, col2_c = st.columns(2)
        with col1_c:
            aporte = st.number_input("Qual o seu Aporte Mensal (R$)?", value=1000.0, step=100.0)
        
        if st.button("Executar Visão do Bosque"):
            # Validação
            total_perc = cart_df["% Cart"].sum()
            if total_perc != 100.0:
                st.warning(f"⚠️ A soma da carteira está em {total_perc}%. Ajuste para fechar 100% exatos.")
            else:
                # Cálculos
                perc_acoes = cart_df[cart_df["Tipo"] == "AÇÕES"]["% Cart"].sum()
                perc_fiis = cart_df[cart_df["Tipo"] == "FIIs"]["% Cart"].sum()
                perc_rf = cart_df[cart_df["Tipo"] == "RENDA FIXA"]["% Cart"].sum()
                
                # C.1 Termômetro do Talmud (1/3 cada)
                dev_acoes = abs(perc_acoes - 33.33)
                dev_fiis = abs(perc_fiis - 33.33)
                dev_rf = abs(perc_rf - 33.33)
                desvio_medio = (dev_acoes + dev_fiis + dev_rf) / 3

                # C.3 Simulador da Grande Virada
                dy_medio_ponderado = (cart_df["DY (%)"] * (cart_df["% Cart"] / 100)).sum()
                pat_virada = (aporte * 12) / (dy_medio_ponderado / 100) if dy_medio_ponderado > 0 else 0

                # --- EXIBIÇÃO ---
                st.markdown("---")
                c_a, c_b, c_c = st.columns(3)
                c_a.metric("Ações", f"{perc_acoes:.1f}%", f"{33.3-perc_acoes:.1f}% do Ideal")
                c_b.metric("FIIs", f"{perc_fiis:.1f}%", f"{33.3-perc_fiis:.1f}% do Ideal")
                c_c.metric("Renda Fixa", f"{perc_rf:.1f}%", f"{33.3-perc_rf:.1f}% do Ideal")

                st.markdown("### ⚖️ C.1 Termômetro do Talmud (Pilar D)")
                st.write(f"**Desvio Médio da Regra de 1/3:** {desvio_medio:.1f} p.p.")
                if desvio_medio <= 5: st.success("🍏 POMAR EQUILIBRADO (Nota 20)")
                elif desvio_medio <= 15: st.warning("🍋 DESEQUILÍBRIO MODERADO (Nota 10)")
                else: st.error("🍎 MONOCULTURA - Risco de Concentração Elevado (Nota 5)")

                st.markdown("### 🌱 C.3 Simulador da Grande Virada")
                st.info(f"**DY Médio da Carteira:** {dy_medio_ponderado:.2f}%")
                st.write(f"Para que a sua carteira gere **R$ {aporte:.2f}/mês** (igualando o seu aporte) de forma totalmente passiva, você precisará atingir:")
                st.success(f"💰 Patrimônio da Virada: **R$ {pat_virada:,.2f}**")
                st.caption("Projeção educacional e matemática. Não constitui garantia de rentabilidade (Cap 8.5.1).")
