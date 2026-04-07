import streamlit as st
import traceback

# 1. ESTA DEVE SER A PRIMEIRA LINHA DO STREAMLIT (Evita tela branca)
st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 SUPREME", page_icon="🌱", layout="wide")

# 2. ARMADURA GLOBAL DE DETECÇÃO DE ERROS
try:
    import pandas as pd
    import requests
    import math
    import re
    from datetime import date, datetime

    # Importações seguras
    try:
        import yfinance as yf
        YF_OK = True
    except ImportError:
        YF_OK = False

    try:
        import google.generativeai as genai
        GENAI_OK = True
    except ImportError:
        GENAI_OK = False

    # CSS e Estética
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
    AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 SUPREME               |
|                                                                      |
|  Exercicio estritamente educacional e matematico.                    |
|  Apendice do livro Metodo R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NAO constitui recomendacao de investimento (Res. CVM 20/2021).      |
|  A decisao de investimento e 100% exclusiva do usuario.              |
+----------------------------------------------------------------------+"""

    RODAPE = """\
----------------------------------------------------------------------------
  R.E.N.D.A. PROTOCOL(TM) V.102.09 FULL (Portfolio Edition)
  (c) Laerson Endrigo Ely, 2026. Todos os direitos reservados.
----------------------------------------------------------------------------"""

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # ── Motores ─────────────────────────────────────────────────────────────
    @st.cache_data(ttl=3600)
    def fetch_macro():
        now = datetime.now().strftime("%d/%m %H:%M")
        try:
            s = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=5).json()[0]["valor"])
            i = float(requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=5).json()[0]["valor"])
            src = "BCB API"
        except:
            s, i, src = 10.75, 4.50, "FALLBACK"
        
        dias = max(0, (date.today() - date(2026, 1, 29)).days)
        copom_min = 276 + int(dias / 45)
        ntnb = round((s - i) * 0.6 + i, 2)
        return {"selic": s, "ipca": i, "ntnb": ntnb, "copom_min": copom_min, "now": now, "src": src}

    def fetch_cotacao(ticker):
        if not YF_OK or not ticker: return 0.0
        try:
            t = ticker.upper().strip()
            tk_obj = yf.Ticker(f"{t}.SA")
            preco = tk_obj.fast_info['lastPrice']
            if preco > 0: return round(preco, 2)
            return round(yf.Ticker(t).fast_info['lastPrice'], 2)
        except: return 0.0

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

    def garimpar_ped(texto):
        t = texto.upper()
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

    def pilar_R(cagr):
        if cagr > 10: return 20, f"CAGR {cagr:.1f}% Frutos Acelerados"
        if cagr > 5: return 15, f"CAGR {cagr:.1f}% Frutos Crescentes"
        if cagr > 0: return 10, f"CAGR {cagr:.1f}% Frutos Estaveis"
        return 5, f"CAGR {cagr:.1f}% Estagnado"

    def pilar_E(setor, tipo):
        s = str(setor).lower()
        if "fii" in tipo.lower():
            fii_ess = ["logist", "saude", "agencia", "educac"]
            fii_mis = ["shopping", "laje", "corporat"]
            fii_cic = ["hotel", "residencial"]
            if any(x in s for x in fii_ess): return 20, "Tijolo Essencial"
            if any(x in s for x in fii_mis): return 15, "Tijolo Misto"
            if any(x in s for x in fii_cic): return 5, "Tijolo Ciclico"
            return 10, "FII Papel Diversificado"
        else:
            ac_per = ["transmissao", "saneamento", "banco", "seguro", "saude"]
            ac_mod = ["eletric", "energia", "distribui", "varejo", "telecom"]
            ac_cic = ["mineracao", "siderurg", "petroleo", "construcao"]
            if any(x in s for x in ac_per): return 20, "Essencial Perene"
            if any(x in s for x in ac_mod): return 15, "Essencial Moderado"
            if any(x in s for x in ac_cic): return 5, "Ciclico"
            return 10, "Semi-Essencial"

    def pilar_N(roe, vac, iad, tipo, liq, de, cagr, tend):
        ctx = ""
        if "ACOES" in tipo:
            if liq < 500000 and de < 1.5 and cagr > 5 and tend != "Decrescente":
                ctx = " (Small Cap)"
            if roe > 20: return 20, f"ROE {roe:.1f}% Fosso Econ. OK{ctx}"
            if roe >= 15: return 15, f"ROE {roe:.1f}% Gestao M. Eficaz{ctx}"
            if roe >= 10: return 10, f"ROE {roe:.1f}% Gestao Eficaz{ctx}"
            return 5, f"ROE {roe:.1f}% Gestao Abaixo{ctx}"
        elif "TIJOLO" in tipo:
            if vac < 5: return 20, f"Vacancia {vac:.1f}% Premium OK"
            if vac <= 10: return 15, f"Vacancia {vac:.1f}% Boa Ocupacao"
            if vac <= 15: return 10, f"Vacancia {vac:.1f}% Moderada"
            return 5, f"Vacancia {vac:.1f}% Risco Elevado"
        else:
            if iad < 1: return 20, f"Inadimp {iad:.1f}% Premium OK"
            if iad <= 3: return 15, f"Inadimp {iad:.1f}% Moderado"
            if iad <= 5: return 10, f"Inadimp {iad:.1f}% Atencao"
            return 5, f"Inadimp {iad:.1f}% Risco Elevado"

    def pilar_A(tipo, lpa, vpa, preco, dy, ntnb):
        if "ACOES" in tipo:
            if lpa <= 0 or vpa <= 0: return 5, "LPA/VPA Negativo - Graham NA"
            vi = math.sqrt(22.5 * lpa * vpa)
            mg = ((vi - preco) / vi) * 100 if vi > 0 else 0
            if mg > 20: return 20, f"Margem {mg:.1f}% (VI R${vi:.2f})"
            if mg > 0: return 15, f"Margem {mg:.1f}% (VI R${vi:.2f})"
            if mg >= -20: return 10, f"Preco > VI {mg:.1f}% (VI R${vi:.2f})"
            return 5, f"Preco > VI (VI R${vi:.2f})"
        elif "TIJOLO" in tipo:
            pvp = preco / vpa if vpa > 0 else 1
            if pvp <= 0.90: return 20, f"P/VP {pvp:.2f} Grande Desconto"
            if pvp <= 1.00: return 15, f"P/VP {pvp:.2f} Proximo Justo"
            if pvp <= 1.10: return 10, f"P/VP {pvp:.2f} Leve Premio"
            return 5, f"P/VP {pvp:.2f} Premio Elevado"
        else:
            spread = dy - ntnb
            if spread > 4: return 20, f"Spread {spread:.2f}% Premio OK"
            if spread >= 2: return 15, f"Spread {spread:.2f}% Premio Adequado"
            if spread > 0: return 10, f"Spread {spread:.2f}% Premio Baixo"
            return 5, f"Spread {spread:.2f}% Sem Premio"

    def fmt_liquidez(val):
        if val >= 1_000_000_000: return f"R$ {val/1e9:.2f} Bilhoes/dia"
        if val >= 1_000_000: return f"R$ {val/1e6:.2f} Milhoes/dia"
        if val >= 1_000: return f"R$ {val/1e3:.1f} mil/dia"
        return f"R$ {val:,.0f}/dia"

    # ── Autenticação ────────────────────────────────────────────────────────
    if not st.session_state["authenticated"]:
        st.code(AVISO_LEGAL, language="text")
        st.title("🔐 Acesso ao Mestre Digital")
        pwd = st.text_input("Chave de Acesso (Pág 324):", type="password")
        if st.button("Validar Semente"):
            if pwd.strip().upper() == SENHA:
                st.session_state["authenticated"] = True; st.rerun()
            else: st.error("Chave inválida.")
        st.stop()

    # ── Interface Principal ─────────────────────────────────────────────────
    MA = fetch_macro()
    j_real = MA["selic"] - MA["ipca"]
    clima = "❄️ INVERNO" if j_real > 10 else "☀️ VERÃO"

    st.code(AVISO_LEGAL, language="text")
    st.markdown(f'<span class="chapter-tag">CAPÍTULO 5.2 - O CLIMA MACRO: {clima}</span>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    s_ui = c1.number_input("Selic (%)", value=MA["selic"])
    i_ui = c2.number_input("IPCA (%)", value=MA["ipca"])
    cp_ui = c3.number_input("COPOM Nº", value=MA["copom_min"])
    nb_ui = c4.number_input("NTN-B IPCA+", value=MA["ntnb"])

    ok_cp = "OK" if cp_ui >= MA["copom_min"] else "OBSOLETO"
    st.code(f"""+---------------+-----------+------------------+--------------+------------------+
| Variavel      | Valor     | Fonte            | Data/Hora    | Prova Sombra     |
+---------------+-----------+------------------+--------------+------------------+
| Selic Meta    | {s_ui:>7.2f}% | {MA['src']:<16} | {MA['now']:<12} | COPOM {int(cp_ui)} {ok_cp:<6} |
| IPCA 12m      | {i_ui:>7.2f}% | BCB/IBGE         | {MA['now']:<12} | [Mes recente]    |
| NTN-B Longa   |IPCA+{nb_ui:.2f}% | Calculado        | {MA['now']:<12} | [Regra D-1]      |
| Juro Real     | {j_real:>7.2f}% | Calculado        | Selic-IPCA   | {clima:<16} |
+---------------+-----------+------------------+--------------+------------------+""", language="text")

    aba_a, aba_c, aba_chat = st.tabs(["🌳 Módulo A: Ticker Único", "🌲 Módulo C: Visão do Bosque", "💬 Fale com o Mestre"])

    with aba_a:
        st.markdown('<span class="chapter-tag">CAPÍTULO 8.6 - O SCORECARD DO CULTIVADOR</span>', unsafe_allow_html=True)
        c_tk, c_tr = st.columns([2,1])
        tk_a = c_tk.text_input("TICKER:", placeholder="Ex: BBAS3").upper().strip()
        trilha = c_tr.selectbox("Natureza:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])

        if tk_a:
            with st.spinner("Buscando cotação em tempo real..."): 
                prc_mercado = fetch_cotacao(tk_a)
            
            txt_a = st.text_area("COLE OS INDICADORES DO INVESTIDOR10 AQUI:", height=150, key=f"txt_{tk_a}")
            ped = garimpar_ped(txt_a) if txt_a else {}

            with st.expander("📝 Gate de Auditoria (Auto-fill ativo)", expanded=True):
                f1, f2, f3, f4 = st.columns(4)
                lpa_f = f1.number_input("LPA (R$)", value=ped.get("lpa",0.0), format="%.4f", key=f"lpa_{tk_a}_{len(txt_a)}")
                vpa_f = f1.number_input("VPA (R$)", value=ped.get("vpa",0.0), format="%.4f", key=f"vpa_{tk_a}_{len(txt_a)}")
                dy_f = f2.number_input("DY (%)", value=ped.get("dy",0.0), key=f"dy_{tk_a}_{len(txt_a)}")
                roe_f = f2.number_input("ROE (%)", value=ped.get("roe",0.0), key=f"roe_{tk_a}_{len(txt_a)}")
                de_f = f3.number_input("D/EBITDA", value=ped.get("de",0.0), key=f"de_{tk_a}_{len(txt_a)}")
                cagr_f = f3.number_input("CAGR (%)", value=ped.get("cagr",0.0), key=f"cagr_{tk_a}_{len(txt_a)}")
                vac_f = f1.number_input("Vacância (%)", value=ped.get("vac",0.0), key=f"vac_{tk_a}_{len(txt_a)}")
                iad_f = f2.number_input("Inadimp. (%)", value=ped.get("iad",0.0), key=f"iad_{tk_a}_{len(txt_a)}")
                liq_s = f4.text_input("Liquidez (Raw):", value=ped.get("liq_raw",""), key=f"liq_{tk_a}_{len(txt_a)}")
                prc_f = f4.number_input("Preço Real (R$)", value=prc_mercado if prc_mercado>0 else 10.0, key=f"prc_{tk_a}")
                tend = f4.selectbox("Tendência Lucros:", ["Crescente", "Estável", "Decrescente 3 anos", "Prejuízo Recorrente"])

            if st.button("🚀 EXECUTAR FASE 2 E 3"):
                liq_v = parse_liquidez(liq_s)
                r_n, r_d = pilar_R(cagr_f)
                e_n, e_d = pilar_E("Automático", trilha)
                n_n, n_d = pilar_N(roe_f, vac_f, iad_f, trilha, liq_v, de_f, cagr_f, tend)
                a_n, a_d = pilar_A(trilha, lpa_f, vpa_f, prc_f, dy_f, nb_ui)
                
                sc = sum([r_n, e_n, n_n, a_n]) / 80 * 100

                st.code(f"""+---------+---------------------+------------+----------------------------------+
| Pilar   | Criterio (Trilha)   | Nota (0-20)| Diagnostico                      |
+---------+---------------------+------------+----------------------------------+
| R       | CAGR DPA            | {r_n:>10} | {r_d:<32} |
| E       | Setor / Segmento    | {e_n:>10} | {e_d:<32} |
| N       | ROE/Vac/Inadim      | {n_n:>10} | {n_d:<32} |
| D       | Desvio Talmud       |   -- (N/A) | (Modulo C - carteira)            |
| A       | Valuation           | {a_n:>10} | {a_d:<32} |
+---------+
