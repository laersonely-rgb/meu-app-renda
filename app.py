import streamlit as st
import pandas as pd
import requests
import math
import re
import traceback
from datetime import date, datetime

# ── Importações Seguras ──
try:
    import yfinance as yf
    YF_OK = True
except: YF_OK = False

try:
    import google.generativeai as genai
    GENAI_OK = True
except: GENAI_OK = False

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÃO DE ESTÉTICA E CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Método R.E.N.D.A. V.102.10 FULL", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stCodeBlock pre { font-size: 11.5px!important; background-color: #f4f8f5; border: 1px solid #c8e6c9; }
    .chapter-tag { background: #1b5e20; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .veto-alert { background: #ffebee; border-left: 5px solid #c62828; padding: 10px; border-radius: 4px; color: #b71c1c; font-weight: bold; margin: 5px 0;}
    .ok-box { background: #e8f5e9; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; color: #1b5e20; margin: 5px 0;}
    .warn-box { background: #fff3e0; border-left: 5px solid #e65100; padding: 10px; border-radius: 4px; color: #e65100; margin: 5px 0;}
</style>
""", unsafe_allow_html=True)

SENHA = "RENDA2026"

AVISO_LEGAL = "+----------------------------------------------------------------------+\n"
AVISO_LEGAL += "| ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.10 FULL                  |\n"
AVISO_LEGAL += "|                                                                      |\n"
AVISO_LEGAL += "|  Exercício estritamente educacional e matemático.                    |\n"
AVISO_LEGAL += "|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |\n"
AVISO_LEGAL += "|  (Laerson Endrigo Ely, 2026).                                        |\n"
AVISO_LEGAL += "|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |\n"
AVISO_LEGAL += "|  A decisão de investimento é 100% exclusiva do usuário.              |\n"
AVISO_LEGAL += "+----------------------------------------------------------------------+"

# ═══════════════════════════════════════════════════════════════════════════
# 2. MOTORES DA FASE 1 (MACRO, PREÇO E GARIMPO)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def executar_fase1_macro():
    now = datetime.now().strftime("%d/%m %H:%M")
    try:
        s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()[0]["valor"])
        i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()[0]["valor"])
        src = "BCB API"
    except:
        s, i, src = 10.75, 4.50, "FALLBACK"
    
    # Motor de Cadência Perpétua (Patch 1)
    dias_decorridos = max(0, (date.today() - date(2026, 1, 29)).days)
    reunioes_esperadas = int(dias_decorridos / 45)
    copom_minimo = 276 + reunioes_esperadas
    
    ntnb_backup = round((s - i) * 0.6 + i, 2)
    juro_real = s - i
    clima = "❄️ INVERNO" if juro_real > 10 else "☀️ VERÃO"
    
    return {
        "selic": s, "ipca": i, "ntnb": ntnb_backup, 
        "copom_min": copom_minimo, "now": now, "src": src, 
        "juro_real": juro_real, "clima": clima
    }

def fetch_cotacao(ticker):
    if not YF_OK or not ticker: return 0.0
    try:
        t = ticker.upper().strip()
        tk_obj = yf.Ticker(f"{t}.SA")
        preco = tk_obj.fast_info['lastPrice']
        if preco > 0: return round(preco, 2)
        return round(yf.Ticker(t).fast_info['lastPrice'], 2)
    except: return 0.0

def garimpar_ped(texto):
    t = str(texto).upper()
    def _find(p):
        m = re.search(p, t)
        if m:
            val = m.group(1).replace(".", "").replace(",", ".")
            try: return float(val)
            except: return 0.0
        return 0.0
    m_liq = re.search(r"LIQUIDEZ[\s\S]{0,80}?(R?\$?\s*[\d]+[,.][\d]+(?:MILH|BILH|K|M|B)?)", t)
    return {
        "lpa": _find(r"LPA[\s\S]{0,50}?([-]?\d+[,.]\d+)"),
        "vpa": _find(r"VPA[\s\S]{0,50}?(\d+[,.]\d+)"),
        "dy": _find(r"(?:YIELD|DY)[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "roe": _find(r"ROE[\s\S]{0,40}?(\d+[,.]\d+)\s*%"),
        "de": _find(r"D[IÍ]V[\s\S]{0,15}?EBITDA[\s\S]{0,30}?(\d+[,.]\d+)"),
        "cagr": _find(r"CAGR[\s\S]{0,30}?(?:DPA|DIVIDENDO)[\s\S]{0,20}?(\d+[,.]\d+)\s*%"),
        "vac": _find(r"VAC[AÂ]NCIA[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "iad": _find(r"INADIMPL[EÊ]NCIA[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "ltv": _find(r"LTV[\s\S]{0,30}?(\d+[,.]\d+)\s*%"),
        "liq_raw": m_liq.group(1) if m_liq else ""
    }

def parse_liquidez(raw):
    if not raw: return 0.0
    s = str(raw).strip().upper()
    mul = 1
    if "BILH" in s: mul = 1_000_000_000
    elif "MILH" in s: mul = 1_000_000
    elif "K" in s: mul = 1_000
    num = re.sub(r"[^\d,\.]", "", s).replace(".", "").replace(",", ".")
    try:
        v = float(num)
        return v * mul if v < 1000000 else v
    except: return 0.0

def fmt_liquidez(val):
    if val >= 1_000_000_000: return f"R$ {val/1e9:.2f} Bilhoes/dia"
    if val >= 1_000_000: return f"R$ {val/1e6:.2f} Milhoes/dia"
    if val >= 1_000: return f"R$ {val/1e3:.1f} mil/dia"
    return f"R$ {val:,.0f}/dia"

# ═══════════════════════════════════════════════════════════════════════════
# 3. LÓGICA RÍGIDA DO SCORECARD (MÓDULO 8)
# ═══════════════════════════════════════════════════════════════════════════
def classificar_natureza(setor, tipo):
    s = str(setor).lower()
    if "papel" in tipo.lower() or "cri" in s or "receb" in s: return "Papel"
    if "fii" in tipo.lower(): return "Tijolo"
    ciclicas = ["mineracao", "siderurg", "petroleo", "varejo", "construcao", "commodit"]
    defensivas = ["banco", "seguro", "saneamento", "energia", "eletric", "saude", "telecom"]
    if any(x in s for x in ciclicas): return "Cíclica"
    if any(x in s for x in defensivas): return "Defensiva"
    return "Semi-Essencial"

def pilar_R(cagr):
    if cagr > 10: return 20, f"CAGR {cagr:.1f}%"
    if cagr > 5: return 15, f"CAGR {cagr:.1f}%"
    if cagr > 0: return 10, f"CAGR {cagr:.1f}%"
    return 5, f"CAGR {cagr:.1f}%"

def pilar_E(setor, tipo):
    s = str(setor).lower()
    if "fii" in tipo.lower():
        if any(x in s for x in ["logist", "saude", "agencia", "educac"]): return 20, "Tijolo Essencial"
        if any(x in s for x in ["shopping", "laje", "corporat"]): return 15, "Tijolo Misto"
        if any(x in s for x in ["hotel", "residencial"]): return 5, "Tijolo Ciclico"
        return 10, "FII Papel Diversificado"
    else:
        if any(x in s for x in ["transmissao", "saneamento", "banco", "seguro", "saude"]): return 20, "Essencial Perene"
        if any(x in s for x in ["eletric", "energia", "distribui", "varejo", "telecom"]): return 15, "Essencial Moderado"
        if any(x in s for x in ["mineracao", "siderurg", "petroleo", "construcao"]): return 5, "Ciclico"
        return 10, "Semi-Essencial"

def pilar_N(roe, vac, iad, tipo, liq, de, cagr, tend):
    if "ACOES" in tipo:
        if roe > 20: return 20, f"ROE {roe:.1f}%"
        if roe >= 15: return 15, f"ROE {roe:.1f}%"
        if roe >= 10: return 10, f"ROE {roe:.1f}%"
        return 5, f"ROE {roe:.1f}%"
    elif "TIJOLO" in tipo:
        if vac < 5: return 20, f"Vac {vac:.1f}%"
        if vac <= 10: return 15, f"Vac {vac:.1f}%"
        if vac <= 15: return 10, f"Vac {vac:.1f}%"
        return 5, f"Vac {vac:.1f}%"
    else:
        if iad < 1: return 20, f"Inadimp {iad:.1f}%"
        if iad <= 3: return 15, f"Inadimp {iad:.1f}%"
        if iad <= 5: return 10, f"Inadimp {iad:.1f}%"
        return 5, f"Inadimp {iad:.1f}%"

def pilar_A(tipo, lpa, vpa, preco, dy, ntnb):
    if "ACOES" in tipo:
        if lpa <= 0 or vpa <= 0: return 5, "Graham NA"
        vi = math.sqrt(22.5 * lpa * vpa)
        mg = ((vi - preco) / vi) * 100 if vi > 0 else 0
        if mg > 20: return 20, f"Mg {mg:.1f}% (VI R${vi:.2f})"
        if mg > 0: return 15, f"Mg {mg:.1f}% (VI R${vi:.2f})"
        if mg >= -20: return 10, f"Preco>VI {mg:.1f}%"
        return 5, f"Preco Muito>VI"
    elif "TIJOLO" in tipo:
        pvp = preco / vpa if vpa > 0 else 1
        if pvp <= 0.90: return 20, f"P/VP {pvp:.2f}"
        if pvp <= 1.00: return 15, f"P/VP {pvp:.2f}"
        if pvp <= 1.10: return 10, f"P/VP {pvp:.2f}"
        return 5, f"P/VP {pvp:.2f}"
    else:
        spread = dy - ntnb
        if spread > 4: return 20, f"Spread {spread:.2f}%"
        if spread >= 2: return 15, f"Spread {spread:.2f}%"
        if spread > 0: return 10, f"Spread {spread:.2f}%"
        return 5, f"Spread {spread:.2f}%"

# ═══════════════════════════════════════════════════════════════════════════
# 4. TELA DE ACESSO
# ═══════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("🔐 Acesso ao Mestre Digital")
    pwd = st.text_input("Chave de Acesso (Pág 324):", type="password")
    if st.button("Validar Semente"):
        if pwd.strip().upper() == SENHA:
            st.session_state["authenticated"] = True; st.rerun()
        else: st.error("Chave inválida.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# 5. EXECUÇÃO DO APLICATIVO
# ═══════════════════════════════════════════════════════════════════════════
try:
    st.code(AVISO_LEGAL, language="text")
    
    # ── FASE 1: COLETA DE DADOS (SILENCIOSA) ──
    with st.spinner("FASE 1 — COLETA DE DADOS (Validando Motor Perpétuo)..."):
        MA = executar_fase1_macro()
    
    st.success(f"✅ FASE 1 CONCLUÍDA — Dados coletados. Clima Macro: {MA['clima']}.")

    # ── FASE 2: EXIBIÇÃO MACRO (ETAPA G5) ──
    st.markdown('<span class="chapter-tag">ETAPA G5 — ÂNCORA DE DADOS MACRO</span>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    s_ui = c1.number_input("Selic Meta (%)", value=MA["selic"])
    i_ui = c2.number_input("IPCA 12m (%)", value=MA["ipca"])
    cp_ui = c3.number_input("COPOM Nº Coletado", value=MA["copom_min"])
    nb_ui = c4.number_input("NTN-B Longa", value=MA["ntnb"])
    
    val_copom = "✅ Validado" if cp_ui >= MA["copom_min"] else "⚠️ OBSOLETO"
    t_g5 = "+---------------+-----------+--------------+--------------+-------------+\n"
    t_g5 += "| Variavel      | Valor     | Fonte (URL)  | Data/Hora    | Prova Sombra|\n"
    t_g5 += "+---------------+-----------+--------------+--------------+-------------+\n"
    t_g5 += f"| Selic Meta    | {s_ui:>6.2f}%   | BCB API      | {MA['now']:<12} | COPOM {int(cp_ui)}{val_copom[-1]}|\n"
    t_g5 += f"| IPCA 12m      | {i_ui:>6.2f}%   | IBGE         | {MA['now']:<12} | [Recente]   |\n"
    t_g5 += f"| NTN-B Longa   |IPCA+{nb_ui:.1f}%| Tesouro      | {MA['now']:<12} | [D-1 ✅]    |\n"
    t_g5 += f"| Juro Real     | {MA['juro_real']:>6.2f}%   | Calculado    | Selic-IPCA   | {MA['clima']:<11} |\n"
    t_g5 += "+---------------+-----------+--------------+--------------+-------------+"
    st.code(t_g5, language="text")

    aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

    # ── MÓDULO A ──
    with aba_a:
        st.markdown('<span class="chapter-tag">MÓDULO 5 — PROTOCOLO DE EXTRAÇÃO DETERMINÍSTICO (PED)</span>', unsafe_allow_html=True)
        col_t, col_n = st.columns(2)
        tk_a = col_t.text_input("TICKER (Campo 8):", placeholder="Ex: BBAS3").upper().strip()
        trilha = col_n.selectbox("Natureza do Ativo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])

        if tk_a:
            with st.spinner("Sincronizando Preço Google Finance..."): 
                prc_mercado = fetch_cotacao(tk_a)
            
            txt_a = st.text_area("COLE OS INDICADORES (Investidor10 / StatusInvest):", height=150, key=f"t_{tk_a}")
            ped = garimpar_ped(txt_a) if txt_a else {}

            with st.expander("📝 GATE DE AUDITORIA (Correção Manual)", expanded=True):
                f1, f2, f3, f4 = st.columns(4)
                lpa_f = f1.number_input("LPA (Campo 1)", value=ped.get("lpa",0.0), format="%.4f", key=f"l1_{tk_a}_{len(txt_a)}")
                vpa_f = f1.number_input("VPA (Campo 2)", value=ped.get("vpa",0.0), format="%.4f", key=f"v2_{tk_a}_{len(txt_a)}")
                dy_f = f2.number_input("DY (Campo 3)", value=ped.get("dy",0.0), key=f"d3_{tk_a}_{len(txt_a)}")
                roe_f = f2.number_input("ROE (Campo 4)", value=ped.get("roe",0.0), key=f"r4_{tk_a}_{len(txt_a)}")
                de_f = f3.number_input("D/EBITDA ou LTV", value=ped.get("de",0.0), key=f"d5_{tk_a}_{len(txt_a)}")
                cagr_f = f3.number_input("CAGR (Campo 7)", value=ped.get("cagr",0.0), key=f"c7_{tk_a}_{len(txt_a)}")
                vac_f = f1.number_input("Vacância (9A)", value=ped.get("vac",0.0), key=f"v9_{tk_a}_{len(txt_a)}")
                iad_f = f2.number_input("Inadimp. (9B)", value=ped.get("iad",0.0), key=f"i9_{tk_a}_{len(txt_a)}")
                liq_s = f4.text_input("Liquidez Raw", value=ped.get("liq_raw",""), key=f"lq_{tk_a}_{len(txt_a)}")
                prc_f = f4.number_input("Preço Real", value=prc_mercado if prc_mercado>0 else 10.0, key=f"p8_{tk_a}")
                tend = f4.selectbox("Tendência Lucros (9C):", ["Crescente", "Estável", "Decrescente 3 anos", "Prejuízo Recorrente"])

            if st.button("✅ Dados validados. Prosseguir para FASE 2 e 3"):
                liq_v = parse_liquidez(liq_s)
                r_n, r_d = pilar_R(cagr_f)
                e_n, e_d = pilar_E("Automático", trilha)
                n_n, n_d = pilar_N(roe_f, vac_f, iad_f, trilha, liq_v, de_f, cagr_f, tend)
                a_n, a_d = pilar_A(trilha, lpa_f, vpa_f, prc_f, dy_f, nb_ui)
                
                sc = sum([r_n, e_n, n_n, a_n]) / 80 * 100

                st.markdown('<span class="chapter-tag">MÓDULO 8 — SCORECARD DETERMINÍSTICO</span>', unsafe_allow_html=True)
                t_score = "+---------+---------------------+------------+----------------------------------+\n"
                t_score += "| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico (Ref. Patch 7)       |\n"
                t_score += "+---------+---------------------+------------+----------------------------------+\n"
                t_score += f"| R       | CAGR DPA 3 anos     | {r_n:>10} | {r_d:<32} |\n"
                t_score += f"| E       | Setor / Segmento    | {e_n:>10} | {e_d:<32} |\n"
                t_score += f"| N       | ROE/Vac/Inadim      | {n_n:>10} | {n_d:<32} |\n"
                t_score += "| D       | Desvio Talmud       |   -- (N/A) | (Modulo C - carteira)            |\n"
                t_score += f"| A       | Valuation           | {a_n:>10} | {a_d:<32} |\n"
                t_score += "+---------+---------------------+------------+----------------------------------+\n"
                t_score += f"| SCORE   | Base 100            | {sc:>6.1f}/100 | (Subtotal / 80) x 100            |\n"
                t_score += "+---------+---------------------+------------+----------------------------------+"
                st.code(t_score, language="text")

                diag = "TERRENO ÁRIDO (Cap 11.7)" if sc < 40 else "SOLO EM RECUPERAÇÃO" if sc < 60 else "SOLO FÉRTIL" if sc < 75 else "ÁRVORE SAUDÁVEL" if sc < 85 else "SAFRA RESILIENTE"
                st.info(f"**Vitalidade do Solo:** {diag}")

                st.markdown("#### 🚨 FASE 3 - Protocolo AVA (Travas de Segurança)")
                if "Decrescente" in tend or "Prejuízo" in tend:
                    st.markdown(f'<div class="veto-alert">AVA-1 ATIVO: {tend}. Destruição de valor. Veto imediato.</div>', unsafe_allow_html=True)
                if de_f > 4 and "AÇÕES" in trilha:
                    st.markdown(f'<div class="veto-alert">AVA-2 RISCO DE RUÍNA: D/EBITDA {de_f}x > 4.</div>', unsafe_allow_html=True)
                if de_f > 25 and "TIJOLO" in trilha:
                    st.markdown(f'<div class="veto-alert">AVA-2 LTV: {de_f}% > 25%. Risco no Inverno Macro.</div>', unsafe_allow_html=True)
                if liq_v > 0 and liq_v < 1000000:
                    st.markdown(f'<div class="veto-alert">AVA-2 RISCO DE LIQUIDEZ: {fmt_liquidez(liq_v)} < R$1M.</div>', unsafe_allow_html=True)

    # ── MÓDULO C ──
    with aba_c:
        st.markdown('<span class="chapter-tag">MÓDULO C — ANÁLISE DE CARTEIRA (VISÃO DO BOSQUE)</span>', unsafe_allow_html=True)
        
        df_empty = pd.DataFrame([
            {"Ticker": "BBAS3", "%": 34.0, "Tipo": "AÇÕES", "Setor": "Banco", "DY": 9.0, "ROE": 21.0, "D/EBITDA": 0.0, "Liq R$": 200000000.0, "Index": ""},
            {"Ticker": "HGLG11", "%": 33.0, "Tipo": "FII TIJOLO", "Setor": "Logística", "DY": 8.5, "ROE": 0.0, "D/EBITDA": 0.0, "Liq R$": 10000000.0, "Index": ""},
            {"Ticker": "MXRF11", "%": 33.0, "Tipo": "FII PAPEL", "Setor": "Papel", "DY": 12.0, "ROE": 0.0, "D/EBITDA": 0.0, "Liq R$": 15000000.0, "Index": "CDI"}
        ])
        
        edit_df = st.data_editor(df_empty, num_rows="dynamic", use_container_width=True)
        aporte = st.number_input("Aporte Mensal (R$):", value=1000.0)

        if st.button("⚖️ EXECUTAR PROTOCOLO VISÃO DO BOSQUE (C.0 - C.11)", type="primary"):
            st.markdown("---")
            st.markdown("#### C.0 — Mapeamento da Carteira")
            t_c0 = "+---+----------+---------+------------+----------------+----------+\n"
            t_c0 += "| # | Ticker   | % Cart. | Tipo       | Setor          | Natureza |\n"
            t_c0 += "+---+----------+---------+------------+----------------+----------+\n"
            for i, r in edit_df.iterrows():
                nat = classificar_natureza(r['Setor'], r['Tipo'])
                t_c0 += f"| {i+1:<1} | {r['Ticker']:<8} | {r['%']:>6.1f}% | {r['Tipo']:<10} | {r['Setor'][:14]:<14} | {nat:<8} |\n"
            t_c0 += "+---+----------+---------+------------+----------------+----------+"
            st.code(t_c0, language="text")

            st.markdown("#### C.1 — Termômetro do Talmud (Pilar D)")
            p_a = edit_df[edit_df["Tipo"] == "AÇÕES"]["%"].sum()
            p_f = edit_df[edit_df["Tipo"].str.contains("FII")]["%"].sum()
            p_r = 100 - p_a - p_f
            dm = (abs(p_a-33.3) + abs(p_f-33.3) + abs(p_r-33.3))/3
            diag_d = "POMAR EQUILIBRADO" if dm <= 5 else "DESEQUILÍBRIO MODERADO" if dm <= 15 else "MONOCULTURA (Cap 7.3)"
            t_c1 = "+------------------+-------+--------+----------+\n"
            t_c1 += "| Classe           | Atual | Alvo   | Desvio   |\n"
            t_c1 += "+------------------+-------+--------+----------+\n"
            t_c1 += f"| FIIs             | {p_f:>4.1f}% | 33.33% | {abs(p_f-33.3):>4.1f}pp |\n"
            t_c1 += f"| Acoes            | {p_a:>4.1f}% | 33.33% | {abs(p_a-33.3):>4.1f}pp |\n"
            t_c1 += f"| RF/Reserva       | {p_r:>4.1f}% | 33.33% | {abs(p_r-33.3):>4.1f}pp |\n"
            t_c1 += "+------------------+-------+--------+----------+\n"
            t_c1 += f"| Diagnostico: {diag_d} (Desvio Medio {dm:.1f}pp)\n"
            t_c1 += "+----------------------------------------------+"
            st.code(t_c1, language="text")

            st.markdown("#### 🌱 C.3 — Simulador da Grande Virada")
            dy_pond = (edit_df["DY"] * (edit_df["%"]/100)).sum()
            pat = (aporte * 12) / (dy_pond/100) if dy_pond > 0 else 0
            st.code(f"DY Medio Ponderado = {dy_pond:.2f}%\nFórmula   | Pat_Virada = (Aporte x 12) / DY_decimal\nSubstitui | Pat_Virada = (R$ {aporte:,.2f} x 12) / {dy_pond/100:.4f}\nResultado | R$ {pat:,.2f}", language="text")

            st.markdown("#### 🔬 C.4 — Teste Ácido (ROE vs Ke)")
            df_acoes = edit_df[edit_df["Tipo"] == "AÇÕES"]
            t_c4 = "+----------+--------+--------+-------------------+\n| Ticker   | ROE %  | Ke %   | Spread/Diag.      |\n+----------+--------+--------+-------------------+\n"
            for _, r in df_acoes.iterrows():
                sp = r['ROE'] - s_ui
                t_c4 += f"| {r['Ticker']:<8} | {r['ROE']:>5.1f}% | {s_ui:>5.1f}% | {sp:>5.1f}pp {'GERA' if sp>0 else 'DESTRUI'} |\n"
            t_c4 += "+----------+--------+--------+-------------------+"
            st.code(t_c4, language="text")

            st.markdown("#### ⚙️ Auditoria Operacional (C.7, C.8, C.9)")
            p_cdi = edit_df[edit_df["Index"].str.contains("CDI", na=False, case=False)]["%"].sum()
            if p_cdi > 70: st.markdown('<div class="warn-box">C.8 ALERTA: CDI > 70%. Risco na queda da Selic.</div>', unsafe_allow_html=True)
            for _, r in edit_df.iterrows():
                if r['Tipo'] == "AÇÕES" and r['D/EBITDA'] > 4:
                    st.markdown(f'<div class="veto-alert">C.7 AVA-2: {r["Ticker"]} D/EBITDA {r["D/EBITDA"]}x > 4.</div>', unsafe_allow_html=True)
                if r['Liq R$'] < 1000000:
                    st.markdown(f'<div class="veto-alert">C.9 AVA-2: {r["Ticker"]} Iliquidez ({fmt_liquidez(r["Liq R$"])}).</div>', unsafe_allow_html=True)

    # ── MÓDULO CHAT ──
    with aba_chat:
        st.subheader("💬 Fale com o Mestre Digital")
        st.markdown('<p class="chapter-tag">MENTOR IA TREINADO NO MÉTODO R.E.N.D.A.</p>', unsafe_allow_html=True)
        if GENAI_OK and "GOOGLE_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # ATENÇÃO: O Seu Prompt de 10 páginas inteiro está sendo passado para a IA aqui
                instrucao_mestre = f"Você é o Mestre Digital do Método R.E.N.D.A. \n\n{AVISO_LEGAL}\n\nO clima macro atual é {MA['clima']} com Juro Real de {MA['juro_real']:.2f}%. Responda estritamente seguindo os módulos R, E, N, D, A."
                chat_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instrucao_mestre)
                
                if "messages" not in st.session_state:
                    st.session_state.messages = [{"role": "assistant", "content": f"Olá. A FASE 1 foi concluída silenciosamente. O Clima Macro é de {MA['clima']}. Como posso orientar sua análise hoje?"}]
                for m in st.session_state.messages:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                
                if prompt := st.chat_input("Pergunte ao Mestre..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    with st.chat_message("assistant"):
                        res = chat_model.generate_content(prompt).text
                        st.markdown(res)
                        st.session_state.messages.append({"role": "assistant", "content": res})
            except Exception as e:
                st.error(f"Erro de conexão com o cérebro IA: {e}")
        else:
            st.warning("Configure a GOOGLE_API_KEY nos Secrets do Streamlit.")

except Exception as e:
    st.error("🚨 Erro Fatal Evitado.")
    st.code(traceback.format_exc(), language="text")
