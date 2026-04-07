import streamlit as st
import pandas as pd
import requests
import math
import re
import json
from datetime import date, datetime
from io import BytesIO

# ── Tentar importar yfinance (opcional) ────────────────────────────────────
try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

# ── Tentar importar fpdf ───────────────────────────────────────────────────
try:
    from fpdf import FPDF
    FPDF_OK = True
except ImportError:
    FPDF_OK = False

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO GLOBAL
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Método R.E.N.D.A. V.102.09 FULL",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .stCodeBlock { font-size: 12px; }
    .block-container { padding-top: 1rem; }
    .ava-alert { background:#ff4b4b22; border-left:4px solid #ff4b4b;
                 padding:0.5rem 1rem; border-radius:4px; margin:0.5rem 0; }
    .ok-box    { background:#00c85322; border-left:4px solid #00c853;
                 padding:0.5rem 1rem; border-radius:4px; margin:0.5rem 0; }
    .warn-box  { background:#ffd60022; border-left:4px solid #ffd600;
                 padding:0.5rem 1rem; border-radius:4px; margin:0.5rem 0; }
</style>
""", unsafe_allow_html=True)

SENHA_CORRETA = "RENDA2026"

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 0 — SAFE HARBOR
# ═══════════════════════════════════════════════════════════════════════════
AVISO_LEGAL = """
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL — O Método R.E.N.D.A. V.102.09 FULL                  |
|                                                                      |
|  Exercício estritamente educacional e matemático.                    |
|  Apêndice do livro Método R.E.N.D.A. de Investimentos                |
|  (Laerson Endrigo Ely, 2026).                                        |
|  NÃO constitui recomendação de investimento (Res. CVM 20/2021).      |
|  A decisão de investimento é 100% exclusiva do usuário.              |
+----------------------------------------------------------------------+
"""

RODAPE = """
----------------------------------------------------------------------------
  R.E.N.D.A. PROTOCOL™ V.102.09 FULL (Portfolio Edition)
  © Laerson Endrigo Ely, 2026. Todos os direitos reservados.
  Exercício educacional — NÃO constitui recomendação de investimento.
----------------------------------------------------------------------------
"""

# ═══════════════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("🔐 Acesso ao Mestre Digital — R.E.N.D.A.")
    col_pwd, col_btn = st.columns([3, 1])
    with col_pwd:
        pwd = st.text_input("Chave de Acesso:", type="password",
                            placeholder="Digite a senha de acesso...")
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔓 Validar Semente", use_container_width=True):
            if pwd == SENHA_CORRETA:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Chave inválida. Tente novamente.")
    st.info("💡 Acesso exclusivo para detentores do livro *Método R.E.N.D.A. de Investimentos* (2026).")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# MOTOR PERPÉTUO — DADOS MACRO (PATCH 1, 2, 3)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_macro():
    """Coleta Selic e IPCA do BCB. Calcula NTN-B backup e validação COPOM."""
    erros = []
    agora = datetime.now().strftime("%d/%m %H:%M")

    # Selic
    try:
        r = requests.get(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1",
            timeout=8)
        selic = float(r.json()[0]['valor'])
        fonte_selic = f"BCB API [{agora}]"
    except Exception as e:
        selic = 10.75
        fonte_selic = f"⚠️ FALLBACK [{agora}]"
        erros.append(f"Selic: {e}")

    # IPCA 12m
    try:
        r = requests.get(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1",
            timeout=8)
        ipca = float(r.json()[0]['valor'])
        fonte_ipca = f"BCB API [{agora}]"
    except Exception as e:
        ipca = 4.50
        fonte_ipca = f"⚠️ FALLBACK [{agora}]"
        erros.append(f"IPCA: {e}")

    # Validação COPOM (Patch 1)
    dias = (date.today() - date(2026, 1, 29)).days
    copom_minimo = 276 + max(0, int(dias / 45))

    # NTN-B backup (Patch 3)
    ntnb_backup = round((selic - ipca) * 0.6 + ipca, 2)

    # Juro real
    juro_real = round(selic - ipca, 2)
    clima = "❄️ INVERNO MACRO" if juro_real > 10 else "☀️ VERÃO MACRO"

    return {
        "selic": selic,
        "ipca": ipca,
        "ntnb": ntnb_backup,
        "copom_minimo": copom_minimo,
        "juro_real": juro_real,
        "clima": clima,
        "fonte_selic": fonte_selic,
        "fonte_ipca": fonte_ipca,
        "agora": agora,
        "erros": erros,
    }


def fetch_preco_yf(ticker: str) -> tuple[float | None, str]:
    """Busca cotação via yfinance. Adiciona .SA se necessário."""
    if not YF_OK:
        return None, "yfinance não instalado"
    try:
        sufixo = ".SA" if not ticker.endswith(".SA") else ""
        t = yf.Ticker(ticker + sufixo)
        hist = t.history(period="1d")
        if hist.empty:
            return None, "Sem dados"
        preco = round(float(hist["Close"].iloc[-1]), 2)
        return preco, f"yFinance [{datetime.now().strftime('%d/%m %H:%M')}]"
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════════════════════
# EXTRAÇÃO DE DADOS DO PED (via texto colado)
# ═══════════════════════════════════════════════════════════════════════════
def extrair_numero(padrao, texto):
    """Extrai primeiro número que case com o padrão."""
    m = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip().replace('.', '').replace(',', '.')
    try:
        return float(raw)
    except ValueError:
        return None

def garimpar_ped(texto: str) -> dict:
    """
    Extrai os 9 campos do PED a partir do texto colado pelo usuário.
    Retorna dicionário com os valores ou None quando indisponível.
    """
    d = {}
    t = texto

    # Campo 1 — LPA
    d['lpa'] = (extrair_numero(r'LPA[\s\S]{0,30}?R?\$?\s*([\-]?[0-9]+[.,][0-9]+)', t)
                or extrair_numero(r'Lucro\s+por\s+A[çc][aã]o[\s\S]{0,30}?([\-]?[0-9]+[.,][0-9]+)', t))

    # Campo 2 — VPA
    d['vpa'] = (extrair_numero(r'VPA[\s\S]{0,30}?R?\$?\s*([0-9]+[.,][0-9]+)', t)
                or extrair_numero(r'Valor\s+Patrimonial[\s\S]{0,30}?([0-9]+[.,][0-9]+)', t))

    # Campo 3 — DY
    d['dy'] = (extrair_numero(r'(?:Dividend\s+Yield|DY)[\s\S]{0,30}?([0-9]+[.,][0-9]+)\s*%', t)
               or extrair_numero(r'DY[\s\S]{0,10}?([0-9]+[.,][0-9]+)', t))

    # Campo 4 — ROE
    d['roe'] = extrair_numero(r'ROE[\s\S]{0,30}?([0-9]+[.,][0-9]+)\s*%', t)

    # Campo 5 — D/EBITDA ou LTV
    d['d_ebitda'] = (extrair_numero(r'D[ií]v\.?\s*L[íi]q\.?\s*/\s*EBITDA[\s\S]{0,30}?([0-9]+[.,][0-9]+)', t)
                     or extrair_numero(r'D/EBITDA[\s\S]{0,20}?([0-9]+[.,][0-9]+)', t))
    d['ltv'] = extrair_numero(r'LTV[\s\S]{0,20}?([0-9]+[.,][0-9]+)\s*%', t)

    # Campo 6 — Liquidez
    d['liquidez'] = extrair_numero(
        r'Liquidez\s+(?:M[eé]dia\s+)?Di[aá]ria[\s\S]{0,40}?R?\$?\s*([0-9]+[.,][0-9]+(?:\.[0-9]+)?)', t)

    # Campo 7 — CAGR DPA
    d['cagr_dpa'] = (extrair_numero(r'CAGR\s+(?:DPA|Dividendos|Provento)[\s\S]{0,30}?([0-9]+[.,][0-9]+)\s*%', t)
                     or extrair_numero(r'CAGR[\s\S]{0,20}?([0-9]+[.,][0-9]+)\s*%', t))

    # Campo 8 — Preço (usado como fallback se yfinance falhar)
    d['preco_colado'] = extrair_numero(
        r'(?:Pre[çc]o\s+Atual|Cota[çc][aã]o|Last)[\s\S]{0,20}?R?\$?\s*([0-9]+[.,][0-9]+)', t)

    # Campo 9A — Vacância
    d['vacancia'] = extrair_numero(r'Vac[âa]ncia[\s\S]{0,20}?([0-9]+[.,][0-9]+)\s*%', t)

    # Campo 9B — Inadimplência
    d['inadimplencia'] = extrair_numero(r'Inadimpl[eê]ncia[\s\S]{0,20}?([0-9]+[.,][0-9]+)\s*%', t)

    # Campo 9C — LPA histórico (3 anos)
    anos = re.findall(r'(?:LPA|Lucro\s+por\s+A[çc][aã]o)[\s\S]{0,5}?(\d{4})[\s\S]{0,10}?([\-]?[0-9]+[.,][0-9]+)', t)
    if anos:
        anos_dict = {}
        for ano, val in anos:
            try:
                anos_dict[int(ano)] = float(val.replace(',', '.'))
            except ValueError:
                pass
        d['lpa_historico'] = dict(sorted(anos_dict.items(), reverse=True))
    else:
        d['lpa_historico'] = {}

    return d


def tendencia_lucros(lpa_hist: dict) -> str:
    """Retorna tendência de lucros baseada no histórico de LPA."""
    if len(lpa_hist) < 3:
        return "[DADO INDISPONÍVEL NO FEED]"
    vals = list(lpa_hist.values())[:3]  # ano1=mais recente
    ano1, ano2, ano3 = vals[0], vals[1], vals[2]
    if any(v < 0 for v in [ano1, ano2, ano3]):
        return "Prejuízo Recorrente 🚨 AVA-1"
    if ano1 > ano2 > ano3:
        return "Crescente ✅"
    if ano1 < ano2 < ano3:
        return "Decrescente 3 anos 🚨 AVA-1"
    variacao_max = max(abs((ano1 - ano2) / ano2 * 100), abs((ano2 - ano3) / ano3 * 100)) if ano2 and ano3 else 100
    if variacao_max <= 10:
        return "Estável ⚠️"
    return "Irregular ⚠️"

# ═══════════════════════════════════════════════════════════════════════════
# SCORECARD — MÓDULO 8 (PATCH 7)
# ═══════════════════════════════════════════════════════════════════════════
def pilar_R(cagr_dpa) -> tuple[int, str]:
    if cagr_dpa is None:
        return 10, "CAGR indisponível → neutro (sem penalidade)"
    if cagr_dpa > 10:
        return 20, f"CAGR {cagr_dpa:.1f}% — Frutos Acelerados ✅"
    if cagr_dpa > 5:
        return 15, f"CAGR {cagr_dpa:.1f}% — Frutos Crescentes"
    if cagr_dpa > 0:
        return 10, f"CAGR {cagr_dpa:.1f}% — Frutos Estáveis ⚠️"
    return 5, f"CAGR {cagr_dpa:.1f}% — Frutos Estagnados 🚨"


SETORES_ESSENCIAIS = {
    20: ["transmissão", "saneamento", "banco", "seguro", "saúde", "seguros",
         "financeiro", "financeira"],
    15: ["elétric", "energia", "geração", "distribui", "telecom", "alimentar",
         "varejo alim", "agua", "água"],
    10: ["logística", "logistica", "indústria", "industria", "transport",
         "carga"],
    5:  ["mineração", "mineracao", "siderurgia", "petroleo", "petróleo",
         "construção", "construcao", "varejo", "commodit", "papel", "celulose"],
}

SEGMENTOS_FII = {
    20: ["logística", "logistica", "saúde", "saude", "agência", "agencia",
         "educaç", "hospital"],
    15: ["shopping", "laje", "lajes corporativas", "cri essencial", "papel essencial"],
    10: ["cri", "papel", "recebíveis", "recebiveis"],
    5:  ["hotel", "residencial", "resort"],
}

def pilar_E(setor: str, tipo: str) -> tuple[int, str]:
    setor_l = setor.lower()
    if tipo == "AÇÕES":
        for pts, palavras in SETORES_ESSENCIAIS.items():
            if any(p in setor_l for p in palavras):
                return pts, f"{setor} — {['Cíclico','Semi-Essencial','Essencial Moderado','Essencial Perene'][list(SETORES_ESSENCIAIS.keys()).index(pts)]}"
        return 10, f"{setor} — Classificação manual recomendada"
    else:  # FII
        for pts, palavras in SEGMENTOS_FII.items():
            if any(p in setor_l for p in palavras):
                return pts, f"{setor} — FII {'Tijolo/Papel'}"
        return 10, f"{setor} — Classificação manual recomendada"


def pilar_N(roe, vacancia, inadimplencia, tipo, liquidez_ok, d_ebitda, cagr_dpa, tend_lucros):
    if tipo == "AÇÕES":
        if roe is None:
            return None, "[DADO INDISPONÍVEL NO FEED]", ""
        contexto_small = ""
        if liquidez_ok and d_ebitda and d_ebitda < 1.5 and cagr_dpa and cagr_dpa > 5:
            if "Crescente" in tend_lucros or "Estável" in tend_lucros:
                contexto_small = f"⚠️ CONTEXTO SMALL CAP: ROE de {roe:.1f}% pode refletir fase de reinvestimento."
        if roe > 20:
            return 20, f"ROE {roe:.1f}% — Fosso Econômico Forte ✅", contexto_small
        if roe >= 15:
            return 15, f"ROE {roe:.1f}% — Gestão Muito Eficaz", contexto_small
        if roe >= 10:
            return 10, f"ROE {roe:.1f}% — Gestão Eficaz", contexto_small
        return 5, f"ROE {roe:.1f}% — Gestão Abaixo do Esperado 🚨", contexto_small
    elif "TIJOLO" in tipo.upper():
        if vacancia is None:
            return None, "[DADO INDISPONÍVEL NO FEED]", ""
        if vacancia < 5:
            return 20, f"Vacância {vacancia:.1f}% — Portfólio Premium ✅", ""
        if vacancia <= 10:
            return 15, f"Vacância {vacancia:.1f}% — Boa Ocupação", ""
        if vacancia <= 15:
            return 10, f"Vacância {vacancia:.1f}% — Ocupação Moderada ⚠️", ""
        return 5, f"Vacância {vacancia:.1f}% — Risco Elevado 🚨", ""
    else:  # PAPEL
        if inadimplencia is None:
            return None, "[DADO INDISPONÍVEL NO FEED]", ""
        if inadimplencia < 1:
            return 20, f"Inadimplência {inadimplencia:.1f}% — Carteira Premium ✅", ""
        if inadimplencia <= 3:
            return 15, f"Inadimplência {inadimplencia:.1f}% — Risco Moderado", ""
        if inadimplencia <= 5:
            return 10, f"Inadimplência {inadimplencia:.1f}% — Atenção ⚠️", ""
        return 5, f"Inadimplência {inadimplencia:.1f}% — Risco Elevado 🚨", ""


def pilar_A_acoes(lpa, vpa, preco) -> tuple[int, str, float | None]:
    if lpa is None or vpa is None or lpa <= 0 or vpa <= 0:
        return 5, "LPA ou VPA negativo/ausente — Graham inaplicável", None
    if preco is None:
        return 5, "Preço indisponível", None
    vi = round(math.sqrt(22.5 * lpa * vpa), 2)
    margem = round(((vi - preco) / vi) * 100, 2)
    if margem > 20:
        return 20, f"Margem {margem:.1f}% — Grande Desconto ✅  VI=R${vi:.2f}", vi
    if margem > 0:
        return 15, f"Margem {margem:.1f}% — Pequeno Desconto  VI=R${vi:.2f}", vi
    if margem >= -20:
        return 10, f"Margem {margem:.1f}% — Leve Prêmio ⚠️  VI=R${vi:.2f}", vi
    return 5, f"Margem {margem:.1f}% — Prêmio Elevado 🚨  VI=R${vi:.2f}", vi


def pilar_A_tijolo(preco, vpa) -> tuple[int, str]:
    if preco is None or vpa is None or vpa == 0:
        return None, "[DADO INDISPONÍVEL NO FEED]"
    pvp = round(preco / vpa, 2)
    if pvp <= 0.90:
        return 20, f"P/VP {pvp:.2f} — Grande Desconto ✅"
    if pvp <= 1.00:
        return 15, f"P/VP {pvp:.2f} — Próximo do Justo"
    if pvp <= 1.10:
        return 10, f"P/VP {pvp:.2f} — Leve Prêmio ⚠️"
    return 5, f"P/VP {pvp:.2f} — Prêmio Elevado 🚨"


def pilar_A_papel(dy, ntnb, clima) -> tuple[int, str]:
    if dy is None or ntnb is None:
        return None, "[DADO INDISPONÍVEL NO FEED]"
    spread = round(dy - ntnb, 2)
    nota_clima = "  (Contexto: Inverno Macro ❄️ — spread pressionado)" if "INVERNO" in clima else ""
    if spread > 4.0:
        return 20, f"Spread {spread:.2f} p.p. — Prêmio Elevado ✅{nota_clima}"
    if spread >= 2.0:
        return 15, f"Spread {spread:.2f} p.p. — Prêmio Adequado{nota_clima}"
    if spread > 0:
        return 10, f"Spread {spread:.2f} p.p. — Prêmio Baixo ⚠️{nota_clima}"
    return 5, f"Spread {spread:.2f} p.p. — Sem Prêmio 🚨{nota_clima}"


def calcular_score(notas: list) -> tuple[float, int]:
    """Score_100 = (soma_notas / pontos_possíveis) x 100"""
    soma = sum(n for n in notas if n is not None)
    possivel = len([n for n in notas if n is not None]) * 20
    if possivel == 0:
        return 0.0, 0
    return round((soma / possivel) * 100, 1), possivel


def diagnostico_score(score: float) -> str:
    if score < 40:
        return "🔴 TERRENO ÁRIDO: Fundamentos críticos. Estudar com extrema cautela. (Cap. 11.7)"
    if score < 60:
        return "🟠 SOLO EM RECUPERAÇÃO: Abaixo do limiar mínimo (60). Revisar pilares < 10."
    if score < 75:
        return "🟡 SOLO FÉRTIL: Base razoável com gaps. Estudar pilares < 15 antes de avançar."
    if score < 85:
        return "🟢 ÁRVORE SAUDÁVEL: Fundamentos sólidos. Próximo do limiar 'o que está esperando?'"
    return "✅ SAFRA RESILIENTE: Alta robustez. Acima do limiar do livro. Estudar margem de segurança."

# ═══════════════════════════════════════════════════════════════════════════
# CLASSIFICAÇÃO DE TIPO E NATUREZA
# ═══════════════════════════════════════════════════════════════════════════
def classificar_natureza(setor: str) -> str:
    s = setor.lower()
    ciclicos = ["mineração","siderurgia","petróleo","construção","varejo","commodit","papel","celulose","transporte"]
    defensivos = ["banco","seguro","saneamento","energia","elétric","telecom","saúde","alimento","água"]
    if any(p in s for p in ciclicos):
        return "Cíclica"
    if any(p in s for p in defensivos):
        return "Defensiva"
    return "Semi-Essencial"

# ═══════════════════════════════════════════════════════════════════════════
# GERAÇÃO DE PDF
# ═══════════════════════════════════════════════════════════════════════════
def gerar_pdf(conteudo: str) -> bytes:
    if not FPDF_OK:
        return b""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=8)
    for linha in conteudo.split('\n'):
        clean = linha.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 4, txt=clean, ln=1)
    return bytes(pdf.output())

# ═══════════════════════════════════════════════════════════════════════════
# FORMATADORES DE TABELA ASCII
# ═══════════════════════════════════════════════════════════════════════════
def fmt_ancora(macro: dict, copom_ui: int) -> str:
    s, i, nb = macro['selic'], macro['ipca'], macro['ntnb']
    jr = macro['juro_real']
    clima = macro['clima']
    agora = macro['agora']
    copom_ok = "✅" if copom_ui >= macro['copom_minimo'] else "🚨 OBSOLETO"
    return f"""
+---------------+-----------+------------------+--------------+------------------+
| Variável      | Valor     | Fonte            | Data/Hora    | Prova Sombra     |
+---------------+-----------+------------------+--------------+------------------+
| Selic Meta    | {s:>7.2f}%  | {macro['fonte_selic']:<16} | {agora:<12} | [COPOM {copom_ui} {copom_ok}]  |
| IPCA 12m      | {i:>7.2f}%  | {macro['fonte_ipca']:<16} | {agora:<12} | [Mês recente]    |
| NTN-B Longa   |IPCA+{nb:.2f}% | Backup Python    | {agora:<12} | [Regra D-1 ⚠️]   |
| Juro Real     | {jr:>7.2f}%  | Calculado        | Selic-IPCA   | [{clima}]|
+---------------+-----------+------------------+--------------+------------------+
"""


def fmt_scorecard(ticker, tipo, r_n, r_d, e_n, e_d, n_n, n_d, a_n, a_d, score, possivel, vi=None) -> str:
    def linha(pilar, criterio, nota, diag):
        n_str = f"{nota:>4}" if nota is not None else "  --"
        d_short = diag[:48] if diag else ""
        return f"| {pilar:<6} | {criterio:<22} | {n_str}/20    | {d_short:<48} |"

    header = f"""
+--------+------------------------+-----------+--------------------------------------------------+
| Pilar  | Critério (Trilha)      | Nota      | Diagnóstico (Ref. Patch 7)                       |
+--------+------------------------+-----------+--------------------------------------------------+
{linha('R', 'CAGR DPA 3 anos', r_n, r_d)}
{linha('E', 'Setor / Segmento', e_n, e_d)}
{linha('N', 'ROE/Vac/Inadim', n_n, n_d)}
| D      | Desvio Talmud          |   --/--   | (Módulo C — carteira)                            |
{linha('A', 'Ver trilha abaixo', a_n, a_d)}
+--------+------------------------+-----------+--------------------------------------------------+
| SUBTOT | Soma bruta             | {sum(x for x in [r_n,e_n,n_n,a_n] if x is not None):>3}/{possivel:<3}     |                                                  |
| SCORE  | Base 100               |  {score:>5}/100 |                                                  |
+--------+------------------------+-----------+--------------------------------------------------+
"""
    return header

# ═══════════════════════════════════════════════════════════════════════════
# ─── INTERFACE PRINCIPAL ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════
st.code(AVISO_LEGAL, language="text")
st.title("🌱 Sistema de Ensino R.E.N.D.A. V.102.09 FULL")
st.caption("Apêndice Digital do livro *Método R.E.N.D.A. de Investimentos* — Laerson Endrigo Ely, 2026")

# ── Sidebar — Botão de logout ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Painel de Controle")
    if st.button("🔒 Sair"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")
    st.markdown("**Versão:** V.102.09 FULL")
    st.markdown("**Módulos:** A (Ticker Único) + C (Carteira)")
    st.markdown("**Motor Macro:** BCB API + PATCH 1/2/3")

# ─────────────────────────────────────────────────────────────────────────
# ETAPA G5 — ÂNCORA MACRO (sempre visível)
# ─────────────────────────────────────────────────────────────────────────
st.subheader("🌐 ETAPA G5 — Âncora de Dados Macro")

macro = fetch_macro()
if macro['erros']:
    st.warning("⚠️ Algumas fontes usaram fallback: " + " | ".join(macro['erros']))

col1, col2, col3, col4 = st.columns(4)
with col1:
    s_ui = st.number_input("Selic Meta (%)", value=macro['selic'], step=0.25, format="%.2f")
with col2:
    i_ui = st.number_input("IPCA 12m (%)", value=macro['ipca'], step=0.1, format="%.2f")
with col3:
    ntnb_ui = st.number_input("NTN-B Longa (IPCA+%)", value=macro['ntnb'], step=0.1, format="%.2f")
with col4:
    cp_ui = st.number_input("Nº Reunião COPOM", value=int(macro['copom_minimo']), step=1)

# Validação COPOM (Patch 1)
if cp_ui < macro['copom_minimo']:
    st.error(f"🚨 DADO OBSOLETO: COPOM {cp_ui} < mínimo esperado {macro['copom_minimo']}. "
             f"Insira o número correto da reunião COPOM.")
    st.stop()

macro_ativo = {**macro, 'selic': s_ui, 'ipca': i_ui, 'ntnb': ntnb_ui,
               'juro_real': round(s_ui - i_ui, 2),
               'clima': "❄️ INVERNO MACRO" if (s_ui - i_ui) > 10 else "☀️ VERÃO MACRO"}

st.code(fmt_ancora(macro_ativo, cp_ui), language="text")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# ABAS
# ─────────────────────────────────────────────────────────────────────────
aba_a, aba_c = st.tabs(["🌳 Módulo A — Ticker Único", "🌲 Módulo C — Visão do Bosque (Carteira)"])

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO A — ANÁLISE DE TICKER ÚNICO
# ═══════════════════════════════════════════════════════════════════════════
with aba_a:
    st.subheader("🔬 Módulo A — Análise de Ativo Único")

    col_t, col_tipo = st.columns([2, 2])
    with col_t:
        ticker = st.text_input("Ticker (ex: TAEE11, MXRF11, ITUB4):", value="").upper().strip()
    with col_tipo:
        tipo = st.selectbox("Trilha de Análise:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"])

    if ticker:
        st.markdown(f"### 📥 FASE 1 — Gate de Auditoria: `{ticker}`")

        # ── Busca de Preço ──────────────────────────────────────────────
        preco_yf, fonte_preco = fetch_preco_yf(ticker)

        col_p, col_fonte = st.columns([2, 3])
        with col_p:
            preco_manual = st.number_input(
                f"Cotação R$ (Google Finance — Patch 8):",
                value=preco_yf if preco_yf else 0.0,
                step=0.01, format="%.2f",
                help="Insira a cotação em tempo real do Google Finance para máxima precisão.")
        with col_fonte:
            st.info(f"**Fonte automática:** {fonte_preco}  \n"
                    f"**Preço capturado:** R$ {preco_yf:.2f}" if preco_yf else
                    f"**Fonte automática:** {fonte_preco}  \nInforme o preço manualmente.")

        preco = preco_manual if preco_manual > 0 else preco_yf

        # ── Setor ───────────────────────────────────────────────────────
        setor = st.text_input("Setor / Segmento do Ativo:",
                              placeholder="Ex: Transmissão Elétrica, Logística, FII Papel CRI...")

        # ── Área de Colagem PED ─────────────────────────────────────────
        st.markdown("#### 📋 Área de Colagem — Investidor10 / StatusInvest")
        st.caption("Cole abaixo o conteúdo copiado da aba Indicadores do Investidor10 ou StatusInvest.")

        txt_ped = st.text_area(
            "Dados do Ativo (PED):", height=200,
            placeholder="Cole aqui os dados do Investidor10, StatusInvest ou relatório do fundo...\n"
                        "O sistema extrai automaticamente: LPA, VPA, DY, ROE, D/EBITDA, Liquidez, CAGR, Vacância/Inadimplência")

        noticia = st.text_input("📰 Título da Notícia Recente (Patch 5 — Verificação Sombra):",
                                placeholder="Cole o título da notícia mais recente da aba do ativo no Investidor10")

        # ── Campos manuais (override) ────────────────────────────────────
        with st.expander("✏️ Inserção / Correção Manual de Campos (sobrescreve extração automática)"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                lpa_m = st.number_input("LPA (R$)", value=0.0, step=0.01, format="%.2f")
                vpa_m = st.number_input("VPA (R$)", value=0.0, step=0.01, format="%.2f")
            with c2:
                dy_m = st.number_input("DY (%)", value=0.0, step=0.1, format="%.2f")
                roe_m = st.number_input("ROE (%)", value=0.0, step=0.1, format="%.2f")
            with c3:
                d_ebitda_m = st.number_input("D/EBITDA (x)", value=0.0, step=0.1, format="%.2f")
                ltv_m = st.number_input("LTV (%) — FII Tijolo", value=0.0, step=0.1, format="%.2f")
            with c4:
                liquidez_m = st.number_input("Liquidez Diária (R$ mil)", value=0.0, step=100.0)
                cagr_m = st.number_input("CAGR DPA (%)", value=0.0, step=0.1, format="%.2f")

            c5, c6 = st.columns(2)
            with c5:
                vac_m = st.number_input("Vacância (%) — FII Tijolo", value=0.0, step=0.1, format="%.2f")
            with c6:
                inad_m = st.number_input("Inadimplência (%) — FII Papel", value=0.0, step=0.1, format="%.2f")

        # ── Botão FASE 2 ────────────────────────────────────────────────
        if st.button("🚀 Executar FASE 2 — Scorecard R.E.N.D.A.", type="primary", use_container_width=True):

            # Extração PED
            ped = garimpar_ped(txt_ped) if txt_ped else {}

            # Hierarquia: manual > PED > None
            def pick(manual_val, ped_key):
                return manual_val if manual_val and manual_val != 0.0 else ped.get(ped_key)

            lpa       = pick(lpa_m, 'lpa')
            vpa       = pick(vpa_m, 'vpa')
            dy        = pick(dy_m, 'dy')
            roe       = pick(roe_m, 'roe')
            d_ebitda  = pick(d_ebitda_m, 'd_ebitda')
            ltv       = pick(ltv_m, 'ltv')
            liquidez  = pick(liquidez_m * 1000 if liquidez_m else 0, 'liquidez')
            cagr_dpa  = pick(cagr_m, 'cagr_dpa')
            vacancia  = pick(vac_m, 'vacancia')
            inadim    = pick(inad_m, 'inadimplencia')
            lpa_hist  = ped.get('lpa_historico', {})

            tend = tendencia_lucros(lpa_hist) if lpa_hist else "[DADO INDISPONÍVEL NO FEED]"
            small_cap = bool(liquidez and liquidez < 500_000)

            # ── Exibir Fase 1 (Gate) ─────────────────────────────────────
            st.markdown("#### 📊 FASE 1 — Gate de Auditoria Completo")

            def fmt_campo(nome, val, unid=""):
                if val is None:
                    return f"| {nome:<35} | {'[DADO INDISPONÍVEL NO FEED]':<30} |"
                return f"| {nome:<35} | {str(val)+unid:<30} |"

            gate = f"""
+-------------------------------------+--------------------------------+
| Campo                               | Valor                          |
+-------------------------------------+--------------------------------+
{fmt_campo('Campo 1 — LPA (R$)', lpa)}
{fmt_campo('Campo 2 — VPA (R$)', vpa)}
{fmt_campo('Campo 3 — DY (%)', dy, '%')}
{fmt_campo('Campo 4 — ROE (%)', roe, '%')}
{fmt_campo('Campo 5 — D/EBITDA (x)', d_ebitda, 'x')}
{fmt_campo('Campo 5 — LTV (%) — FII Tijolo', ltv, '%')}
{fmt_campo('Campo 6 — Liquidez Diária (R$)', liquidez)}
{fmt_campo('Campo 7 — CAGR DPA (%)', cagr_dpa, '%')}
{fmt_campo('Campo 8 — Preço Google (R$)', preco)}
{fmt_campo('Campo 9A — Vacância (%)', vacancia, '%')}
{fmt_campo('Campo 9B — Inadimplência (%)', inadim, '%')}
{fmt_campo('Campo 9C — Tendência Lucros 3a', tend)}
+-------------------------------------+--------------------------------+
| Patch 5 — Notícia Sombra            | {'✅ '+noticia[:40] if noticia else '⚠️ NÃO INFORMADO':<30} |
| Patch 8 — Preço Google Sincron.     | {'✅ R$ '+str(preco) if preco else '⚠️ MANUAL':<30} |
| Âncora Macro                        | {'✅ CONSISTENTE':<30} |
+-------------------------------------+--------------------------------+
"""
            st.code(gate, language="text")

            # ── FASE 2 — Scorecard ────────────────────────────────────────
            st.markdown("#### 🏆 FASE 2 — Scorecard R.E.N.D.A. (Patch 7)")

            r_nota, r_diag = pilar_R(cagr_dpa)
            e_nota, e_diag = pilar_E(setor if setor else "N/D", tipo)
            n_nota, n_diag, n_ctx = pilar_N(roe, vacancia, inadim, tipo,
                                             small_cap, d_ebitda, cagr_dpa, tend)

            if tipo == "AÇÕES":
                a_nota, a_diag, vi_calc = pilar_A_acoes(lpa, vpa, preco)
            elif tipo == "FII TIJOLO":
                a_nota, a_diag = pilar_A_tijolo(preco, vpa)
                vi_calc = None
            else:
                a_nota, a_diag = pilar_A_papel(dy, ntnb_ui, macro_ativo['clima'])
                vi_calc = None

            notas = [r_nota, e_nota, n_nota, a_nota]
            score, possivel = calcular_score(notas)
            diag_score = diagnostico_score(score)

            st.code(fmt_scorecard(ticker, tipo,
                                  r_nota, r_diag, e_nota, e_diag,
                                  n_nota, n_diag, a_nota, a_diag,
                                  score, possivel, vi_calc), language="text")

            # Barra visual
            cor = "normal" if score >= 75 else ("off" if score < 60 else "inverse")
            st.progress(int(score) / 100)
            st.markdown(f"**Score Final: {score}/100** — {diag_score}")

            if n_ctx:
                st.markdown(f'<div class="warn-box">{n_ctx}</div>', unsafe_allow_html=True)

            # ── FASE 3 — Diagnósticos AVA ────────────────────────────────
            st.markdown("#### 🚨 FASE 3 — Protocolo AVA (Travas de Segurança)")

            avas = []

            # AVA-1
            if "AVA-1" in tend:
                avas.append(f"🚨 **AVA-1 ATIVO**: {tend} — Prejuízo recorrente ou lucros decrescentes 3 anos. Veto imediato. (Cap. 11.7)")

            # AVA-2 Dívida
            if d_ebitda and d_ebitda > 4:
                avas.append(f"🚨 **AVA-2 RISCO DE RUÍNA**: D/EBITDA {d_ebitda:.1f}x > 4x. Risco de corte de dividendos. (Cap. 11.7)")
            elif d_ebitda and d_ebitda > 3:
                avas.append(f"⚠️ **AVA-2 ATENÇÃO**: D/EBITDA {d_ebitda:.1f}x > 3x. Monitorar endividamento.")

            # AVA-2 LTV
            if ltv and ltv > 25:
                avas.append(f"🚨 **AVA-2 RISCO DE RUÍNA**: LTV {ltv:.1f}% > 25% — despesa financeira pode devorar aluguéis. (Cap. 11.7)")

            # AVA-2 Liquidez
            if liquidez and liquidez < 1_000_000:
                avas.append(f"🚨 **AVA-2 RISCO DE LIQUIDEZ**: Liquidez R${liquidez:,.0f}/dia < R$1M. Saída sem impacto improvável.")

            # ROE vs Ke (C.4)
            if tipo == "AÇÕES" and roe is not None:
                spread_valor = roe - s_ui
                if spread_valor < 0:
                    avas.append(f"⚠️ **TESTE ÁCIDO**: ROE {roe:.1f}% < Ke (Selic {s_ui:.1f}%). Spread: {spread_valor:.1f}%. Verificar Campo 9C. (Cap. 6.1)")
                else:
                    st.markdown(f'<div class="ok-box">✅ <b>Geração de Valor</b>: ROE {roe:.1f}% > Ke {s_ui:.1f}%. Spread: +{spread_valor:.1f}%</div>', unsafe_allow_html=True)

            if avas:
                for ava in avas:
                    st.markdown(f'<div class="ava-alert">{ava}</div>', unsafe_allow_html=True)
            else:
                if tipo == "AÇÕES":
                    st.markdown('<div class="ok-box">✅ Nenhum AVA acionado nesta análise.</div>', unsafe_allow_html=True)

            # ── Graham Radar ──────────────────────────────────────────────
            if tipo == "AÇÕES" and vi_calc:
                st.markdown("#### 📐 Radar de Margem de Segurança — Graham (Cap. 6.5)")
                margem_g = round(((vi_calc - preco) / vi_calc) * 100, 2) if preco else None
                graham_txt = f"""
Fórmula   | VI = √(22,5 × LPA × VPA)
Substitui | VI = √(22,5 × {lpa:.2f} × {vpa:.2f})
Resultado | R$ {vi_calc:.2f}

Margem    | ((VI − Preço) / VI) × 100
Substitui | (({vi_calc:.2f} − {preco:.2f}) / {vi_calc:.2f}) × 100
Resultado | {margem_g:.2f}%

{'✅ MARGEM DE SEGURANÇA PRESENTE.' if margem_g and margem_g > 0 else '⚠️ AUSÊNCIA DE MARGEM: preço acima do VI teórico.'}
⚠️ Referência teórica. Calibrado para EUA anos 1970. (Cap. 6.5 / 6.7.3)
"""
                st.code(graham_txt, language="text")

            # ── Rodapé e PDF ──────────────────────────────────────────────
            st.markdown("---")
            conteudo_pdf = (
                AVISO_LEGAL + "\n\n"
                + f"TICKER: {ticker} | TIPO: {tipo}\n"
                + fmt_ancora(macro_ativo, cp_ui)
                + gate
                + fmt_scorecard(ticker, tipo,
                                r_nota, r_diag, e_nota, e_diag,
                                n_nota, n_diag, a_nota, a_diag,
                                score, possivel, vi_calc)
                + f"\nScore Final: {score}/100\n{diag_score}\n"
                + "\n".join(avas)
                + "\n" + RODAPE
            )

            if FPDF_OK:
                pdf_bytes = gerar_pdf(conteudo_pdf)
                st.download_button(
                    "📄 Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name=f"RENDA_{ticker}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            st.code(RODAPE, language="text")

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO C — CARTEIRA (VISÃO DO BOSQUE)
# ═══════════════════════════════════════════════════════════════════════════
with aba_c:
    st.subheader("🌲 Módulo C — Visão do Bosque (Análise de Carteira)")
    st.caption("Protocolo 'Visão do Bosque' — sem pausas, análise consolidada de todos os ativos.")

    st.markdown("#### 📋 Monte sua Carteira")
    st.info("Adicione até 20 ativos. A soma dos percentuais deve totalizar 100%.")

    # ── Input da carteira ──────────────────────────────────────────────────
    n_ativos = st.number_input("Número de ativos na carteira:", min_value=2, max_value=20, value=4)

    aporte_mensal = st.number_input(
        "💰 Aporte Mensal (R$) — para Simulador da Grande Virada (C.3):",
        min_value=0.0, value=1000.0, step=100.0)

    ativos = []
    total_pct = 0.0

    st.markdown("#### 📊 Dados dos Ativos")
    for i in range(int(n_ativos)):
        with st.expander(f"Ativo {i+1}", expanded=(i < 3)):
            cc1, cc2, cc3, cc4 = st.columns([2, 1, 2, 1])
            with cc1:
                tk = st.text_input(f"Ticker {i+1}:", key=f"tk_{i}").upper().strip()
            with cc2:
                pct = st.number_input(f"% Carteira:", min_value=0.0, max_value=100.0,
                                      step=5.0, key=f"pct_{i}")
            with cc3:
                tipo_i = st.selectbox("Tipo:", ["AÇÕES", "FII TIJOLO", "FII PAPEL"],
                                      key=f"tipo_{i}")
            with cc4:
                setor_i = st.text_input("Setor:", key=f"setor_{i}",
                                        placeholder="Ex: Transmissão")

            cc5, cc6, cc7, cc8 = st.columns(4)
            with cc5:
                lpa_i = st.number_input("LPA (R$)", value=0.0, step=0.01,
                                        format="%.2f", key=f"lpa_{i}")
                vpa_i = st.number_input("VPA (R$)", value=0.0, step=0.01,
                                        format="%.2f", key=f"vpa_{i}")
            with cc6:
                dy_i = st.number_input("DY (%)", value=0.0, step=0.1,
                                       format="%.2f", key=f"dy_{i}")
                roe_i = st.number_input("ROE (%)", value=0.0, step=0.1,
                                        format="%.2f", key=f"roe_{i}")
            with cc7:
                d_ebitda_i = st.number_input("D/EBITDA (x)", value=0.0, step=0.1,
                                             format="%.2f", key=f"deb_{i}")
                vac_i = st.number_input("Vacância (%)", value=0.0, step=0.1,
                                        format="%.2f", key=f"vac_{i}")
            with cc8:
                inad_i = st.number_input("Inadimplência (%)", value=0.0, step=0.1,
                                         format="%.2f", key=f"iad_{i}")
                cagr_i = st.number_input("CAGR DPA (%)", value=0.0, step=0.1,
                                         format="%.2f", key=f"cagr_{i}")

            preco_i_yf, _ = fetch_preco_yf(tk) if tk else (None, "")
            preco_i = st.number_input(
                f"Cotação R$:", value=preco_i_yf if preco_i_yf else 0.0,
                step=0.01, format="%.2f", key=f"preco_{i}",
                help="Preencha com cotação do Google Finance (Patch 8)")

            if tk and pct > 0:
                ativos.append({
                    "ticker": tk, "pct": pct, "tipo": tipo_i, "setor": setor_i,
                    "lpa": lpa_i or None, "vpa": vpa_i or None,
                    "dy": dy_i or None, "roe": roe_i or None,
                    "d_ebitda": d_ebitda_i or None, "vacancia": vac_i or None,
                    "inadimplencia": inad_i or None, "cagr_dpa": cagr_i or None,
                    "preco": preco_i or preco_i_yf,
                })
                total_pct += pct

    # Validação de soma
    if ativos:
        if abs(total_pct - 100.0) > 0.5:
            st.warning(f"⚠️ Soma dos percentuais = {total_pct:.1f}%. Deve ser 100%.")

    if st.button("🌲 Executar Visão do Bosque — Módulo C", type="primary",
                 use_container_width=True, disabled=len(ativos) < 2):

        st.markdown("---")
        st.markdown("### 🗺️ C.0 — Mapeamento da Carteira")

        # C.0 — Tabela de mapeamento
        mapa = "+---+----------+-----------+----------+----------------------+----------+\n"
        mapa += "| # | Ticker   | % Cart.   | Tipo     | Setor                | Natureza |\n"
        mapa += "+---+----------+-----------+----------+----------------------+----------+\n"
        for idx, a in enumerate(ativos):
            nat = ("Papel" if "PAPEL" in a['tipo'].upper()
                   else "Tijolo" if "TIJOLO" in a['tipo'].upper()
                   else classificar_natureza(a['setor']))
            nat_short = nat[:8]
            setor_short = a['setor'][:20] if a['setor'] else "N/D"
            mapa += f"| {idx+1:<1} | {a['ticker']:<8} | {a['pct']:>6.1f}%   | {a['tipo'][:8]:<8} | {setor_short:<20} | {nat_short:<8} |\n"
            a['natureza'] = nat
        mapa += "+---+----------+-----------+----------+----------------------+----------+\n"
        mapa += "⚠️ Classificação indicativa. Verificar empresas multisetoriais.\n"
        st.code(mapa, language="text")

        # C.1 — Talmud
        st.markdown("### ⚖️ C.1 — Termômetro do Talmud (Pilar D)")
        pct_fii = sum(a['pct'] for a in ativos if "FII" in a['tipo'].upper())
        pct_acoes = sum(a['pct'] for a in ativos if a['tipo'] == "AÇÕES")
        pct_rf = max(0, 100 - pct_fii - pct_acoes)
        dev_fii = abs(pct_fii - 33.33)
        dev_acoes = abs(pct_acoes - 33.33)
        dev_rf = abs(pct_rf - 33.33)
        dev_medio = round((dev_fii + dev_acoes + dev_rf) / 3, 1)

        if dev_medio <= 5:
            talmud_diag = "🌳 POMAR EQUILIBRADO (desvio ≤ 5 p.p.)"
            talmud_nota = 20
        elif dev_medio <= 15:
            talmud_diag = "⚠️ DESEQUILÍBRIO MODERADO (desvio 6-15 p.p.)"
            talmud_nota = 10
        else:
            talmud_diag = "🚨 MONOCULTURA (desvio > 15 p.p.) — Risco de concentração (Cap. 7.3)"
            talmud_nota = 5

        talmud_txt = f"""
+------------------+-------+--------+----------+-----------------------------------+
| Classe           | Atual | Alvo   | Desvio   | Status                            |
+------------------+-------+--------+----------+-----------------------------------+
| FIIs             |{pct_fii:>5.1f}% | 33,33% | {dev_fii:>5.1f} p.p | {'✅' if dev_fii<=5 else '⚠️' if dev_fii<=15 else '🚨'}                               |
| Ações            |{pct_acoes:>5.1f}% | 33,33% | {dev_acoes:>5.1f} p.p | {'✅' if dev_acoes<=5 else '⚠️' if dev_acoes<=15 else '🚨'}                               |
| RF/Reserva       |{pct_rf:>5.1f}% | 33,33% | {dev_rf:>5.1f} p.p | {'✅' if dev_rf<=5 else '⚠️' if dev_rf<=15 else '🚨'}                               |
+------------------+-------+--------+----------+-----------------------------------+
| Desvio Médio     |                   {dev_medio:>5.1f} p.p | {talmud_diag:<33} |
+------------------+-------------------+----------+-----------------------------------+
"""
        st.code(talmud_txt, language="text")

        # C.2 — Scorecard Consolidado
        st.markdown("### 📊 C.2 — Scorecard Consolidado R.E.N.D.A.")

        scores_tabela = []
        score_ponderado_total = 0.0

        for a in ativos:
            r_n, _ = pilar_R(a['cagr_dpa'])
            e_n, _ = pilar_E(a['setor'] or "N/D", a['tipo'])
            n_n, _, _ = pilar_N(a['roe'], a['vacancia'], a['inadimplencia'],
                                 a['tipo'], False, a['d_ebitda'],
                                 a['cagr_dpa'], "[FEED]")
            if a['tipo'] == "AÇÕES":
                a_n, _, _ = pilar_A_acoes(a['lpa'], a['vpa'], a['preco'])
            elif a['tipo'] == "FII TIJOLO":
                a_n, _ = pilar_A_tijolo(a['preco'], a['vpa'])
            else:
                a_n, _ = pilar_A_papel(a['dy'], ntnb_ui, macro_ativo['clima'])

            sc, pp = calcular_score([r_n, e_n, n_n, a_n])
            scores_tabela.append({
                "ticker": a['ticker'], "pct": a['pct'],
                "r": r_n, "e": e_n, "n": n_n, "d": talmud_nota, "a": a_n,
                "score": sc
            })
            score_ponderado_total += sc * (a['pct'] / 100)

        score_pond = round(score_ponderado_total, 1)

        sc_txt = "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        sc_txt += "| Ticker   |  %   |  R  |  E  |  N  |  D  |  A  | Score |\n"
        sc_txt += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        for s in scores_tabela:
            r = s['r'] if s['r'] else '--'
            e = s['e'] if s['e'] else '--'
            n = s['n'] if s['n'] else '--'
            a = s['a'] if s['a'] else '--'
            sc_txt += f"| {s['ticker']:<8} |{s['pct']:>4.0f}% | {str(r):>3} | {str(e):>3} | {str(n):>3} | {str(s['d']):>3} | {str(a):>3} | {s['score']:>5.1f} |\n"
        sc_txt += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        sc_txt += f"| PONDERADO|  100%|                               | {score_pond:>5.1f} |\n"
        sc_txt += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        sc_txt += f"{diagnostico_score(score_pond)}\n"
        st.code(sc_txt, language="text")
        st.progress(int(score_pond) / 100)

        # C.3 — Grande Virada
        st.markdown("### 🌱 C.3 — Simulador da Grande Virada")
        dy_pond = sum(
            (a['dy'] or 0) * (a['pct'] / 100)
            for a in ativos
        )
        if dy_pond > 0 and aporte_mensal > 0:
            pat_virada = round((aporte_mensal * 12) / (dy_pond / 100), 2)
            gv_txt = f"""
DY Médio Ponderado = Σ(DY_i × % Cart_i) = {dy_pond:.2f}%

Fórmula   | Pat_Virada = (Aporte × 12) / DY_decimal
Substitui | Pat_Virada = (R$ {aporte_mensal:,.2f} × 12) / {dy_pond/100:.4f}
Resultado | R$ {pat_virada:,.2f}

→ Com R$ {pat_virada:,.2f} em carteira, os dividendos IGUALAM seu aporte anual.
→ Para SUPERAR: aplicar fator 1,2 → R$ {pat_virada*1.2:,.2f}
⚠️ Projeção educacional e matemática. NÃO constitui garantia. (Cap. 8.5.1)
"""
            st.code(gv_txt, language="text")
        else:
            st.info("Informe o Aporte Mensal e DY dos ativos para calcular a Grande Virada.")

        # C.4 — Teste Ácido (apenas ações)
        acoes_c4 = [a for a in ativos if a['tipo'] == "AÇÕES" and a['roe']]
        if acoes_c4:
            st.markdown("### ⚗️ C.4 — Teste Ácido de Destruição de Valor (ROE vs Ke)")
            c4_txt = "+----------+--------+--------+------------------+---------------------+\n"
            c4_txt += "| Ticker   | ROE %  | Ke %   | Spread Valor     | Diagnóstico         |\n"
            c4_txt += "+----------+--------+--------+------------------+---------------------+\n"
            for a in acoes_c4:
                spread = round(a['roe'] - s_ui, 2)
                diag_c4 = "✅ Geração de Valor" if spread > 0 else "⚠️ Destruição de Valor"
                c4_txt += f"| {a['ticker']:<8} | {a['roe']:>5.1f}% | {s_ui:>5.1f}% | {('+' if spread>0 else '')}{spread:>8.2f} p.p | {diag_c4:<19} |\n"
            c4_txt += "+----------+--------+--------+------------------+---------------------+\n"
            st.code(c4_txt, language="text")

        # C.5 — Radar Graham (ações)
        acoes_c5 = [a for a in ativos if a['tipo'] == "AÇÕES"
                    and a['lpa'] and a['lpa'] > 0 and a['vpa'] and a['vpa'] > 0]
        if acoes_c5:
            st.markdown("### 📐 C.5 — Radar de Margem de Segurança (Graham)")
            c5_txt = "+----------+---------+---------+----------+----------+---------------------+\n"
            c5_txt += "| Ticker   | LPA     | VPA     | VI       | Preço    | Margem              |\n"
            c5_txt += "+----------+---------+---------+----------+----------+---------------------+\n"
            for a in acoes_c5:
                vi_c5 = round(math.sqrt(22.5 * a['lpa'] * a['vpa']), 2)
                if a['preco']:
                    mg = round(((vi_c5 - a['preco']) / vi_c5) * 100, 2)
                    mg_str = f"{mg:+.1f}%"
                else:
                    mg_str = "S/preço"
                c5_txt += f"| {a['ticker']:<8} | {a['lpa']:>7.2f} | {a['vpa']:>7.2f} | {vi_c5:>8.2f} | {(a['preco'] or 0):>8.2f} | {mg_str:<19} |\n"
            c5_txt += "+----------+---------+---------+----------+----------+---------------------+\n"
            st.code(c5_txt, language="text")

        # C.6 — Matriz de Ciclicidade
        st.markdown("### 🔄 C.6 — Matriz de Ciclicidade")
        pct_ciclica = sum(a['pct'] for a in ativos if a.get('natureza') == 'Cíclica')
        pct_defensiva = sum(a['pct'] for a in ativos if a.get('natureza') == 'Defensiva')
        pct_outro = 100 - pct_ciclica - pct_defensiva

        if pct_ciclica <= 30:
            cicl_diag = "🌿 FLORESTA RESILIENTE (cíclica ≤ 30%)"
        elif pct_ciclica <= 50:
            cicl_diag = "⚠️ FLORESTA MISTA — monitorar (cíclica 31-50%)"
        else:
            cicl_diag = "🚨 ALERTA DE VOLATILIDADE EXTREMA (cíclica > 50%)"

        c6_txt = f"""
+-------------------+--------+---------------------------------------+
| Natureza          |   %    | Diagnóstico                           |
+-------------------+--------+---------------------------------------+
| Cíclica           |{pct_ciclica:>5.1f}%  | {cicl_diag:<37} |
| Defensiva/Essenc. |{pct_defensiva:>5.1f}%  |                                       |
| FII/Semi-Essenc.  |{pct_outro:>5.1f}%  |                                       |
+-------------------+--------+---------------------------------------+
⚠️ Classificação indicativa. Empresas multisetoriais: verificar manualmente.
"""
        st.code(c6_txt, language="text")

        # C.7 — Asfixia Financeira (ações)
        acoes_c7 = [a for a in ativos if a['tipo'] == "AÇÕES" and a['d_ebitda']]
        if acoes_c7:
            st.markdown("### 💸 C.7 — Teste de Asfixia Financeira (D/EBITDA)")
            c7_txt = "+----------+----------+--------------------------------------+\n"
            c7_txt += "| Ticker   | D/EBITDA | Diagnóstico                          |\n"
            c7_txt += "+----------+----------+--------------------------------------+\n"
            for a in acoes_c7:
                de = a['d_ebitda']
                if de <= 2.0:
                    d7 = "✅ RAÍZES PROFUNDAS"
                elif de <= 3.0:
                    d7 = "⚠️ ALAVANCAGEM MODERADA"
                elif de <= 4.0:
                    d7 = "⚠️ ALAVANCAGEM ELEVADA"
                else:
                    d7 = "🚨 AVA-2 RISCO DE RUÍNA"
                c7_txt += f"| {a['ticker']:<8} | {de:>7.1f}x | {d7:<36} |\n"
            c7_txt += "+----------+----------+--------------------------------------+\n"
            st.code(c7_txt, language="text")

        # C.8 — Raio-X Indexadores
        st.markdown("### 🧭 C.8 — Raio-X de Indexadores")
        pct_cdi = sum(a['pct'] for a in ativos if "PAPEL" in a['tipo'].upper())
        pct_ipca = sum(a['pct'] for a in ativos if a['tipo'] in ["AÇÕES", "FII TIJOLO"])
        c8_txt = f"""
+-------------------+--------+------------------------------------------+
| Indexador         |   %    | Alerta                                   |
+-------------------+--------+------------------------------------------+
| CDI (FII Papel)   |{pct_cdi:>5.1f}%  | {'🚨 ALERTA: CDI>70% — sensível à queda Selic' if pct_cdi>70 else '✅ OK':<40} |
| IPCA+/Operacional |{pct_ipca:>5.1f}%  |                                          |
+-------------------+--------+------------------------------------------+
"""
        st.code(c8_txt, language="text")

        # C.9 — Liquidez
        st.markdown("### 💧 C.9 — Filtro de Liquidez Diária")
        st.info("Verifique a liquidez média diária de cada ativo individualmente na plataforma de dados.")

        # C.11 — LTV FIIs Tijolo
        fiis_tijolo = [a for a in ativos if "TIJOLO" in a['tipo'].upper()]
        if fiis_tijolo:
            st.markdown("### 🏗️ C.11 — Termômetro de Alavancagem FII (LTV)")
            st.info("Informe o LTV de cada FII de Tijolo. Disponível no relatório gerencial mensal do fundo.")

        # Rodapé PDF consolidado
        st.markdown("---")
        st.code(RODAPE, language="text")

        if FPDF_OK:
            relat = (AVISO_LEGAL + "\nMÓDULO C — VISÃO DO BOSQUE\n"
                     + fmt_ancora(macro_ativo, cp_ui)
                     + "\n" + mapa + "\n" + sc_txt
                     + f"\nScore Ponderado: {score_pond}/100\n"
                     + diagnostico_score(score_pond)
                     + "\n" + RODAPE)
            pdf_c = gerar_pdf(relat)
            st.download_button(
                "📄 Baixar Relatório Consolidado PDF",
                data=pdf_c,
                file_name=f"RENDA_Carteira_{date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
