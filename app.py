import streamlit as st
import requests
import math
import re
from datetime import date, datetime

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

try:
    from fpdf import FPDF
    FPDF_OK = True
except ImportError:
    FPDF_OK = False

st.set_page_config(page_title="Método R.E.N.D.A. V.102.09 FULL", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.stCodeBlock pre{font-size:11.5px!important}
.block-container{padding-top:1rem}
.ava-alert{background:#ff4b4b22;border-left:4px solid #ff4b4b;padding:.6rem 1rem;border-radius:4px;margin:.4rem 0}
.ok-box{background:#00c85322;border-left:4px solid #00c853;padding:.6rem 1rem;border-radius:4px;margin:.4rem 0}
.warn-box{background:#ffd60022;border-left:4px solid #ffd600;padding:.6rem 1rem;border-radius:4px;margin:.4rem 0}
.info-box{background:#2979ff22;border-left:4px solid #2979ff;padding:.6rem 1rem;border-radius:4px;margin:.4rem 0}
</style>""", unsafe_allow_html=True)

SENHA = "RENDA2026"
AVISO_LEGAL = """\
+----------------------------------------------------------------------+
| ⚠️  AVISO LEGAL - O Metodo R.E.N.D.A. V.102.09 FULL                  |
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
  Exercicio educacional - NAO constitui recomendacao de investimento.
----------------------------------------------------------------------------"""

# ── Auth ────────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.code(AVISO_LEGAL, language="text")
    st.title("Acesso ao Mestre Digital - R.E.N.D.A.")
    c1, c2 = st.columns([3, 1])
    pwd = c1.text_input("Chave de Acesso:", type="password")
    c2.write(""); c2.write("")
    if c2.button("Validar", use_container_width=True):
        if pwd == SENHA:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Chave invalida.")
    st.stop()

# ── Macro ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_macro():
    now = datetime.now().strftime("%d/%m %H:%M")
    erros = []
    try:
        r = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1", timeout=8)
        selic = float(r.json()[0]["valor"])
        src_s = f"BCB API [{now}]"
    except Exception as e:
        selic, src_s = 10.75, f"FALLBACK [{now}]"
        erros.append(str(e))
    try:
        r = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1", timeout=8)
        ipca = float(r.json()[0]["valor"])
        src_i = f"BCB API [{now}]"
    except Exception as e:
        ipca, src_i = 4.50, f"FALLBACK [{now}]"
        erros.append(str(e))
    dias = max(0, (date.today() - date(2026, 1, 29)).days)
    copom_min = 276 + int(dias / 45)
    ntnb = round((selic - ipca) * 0.6 + ipca, 2)
    juro_real = round(selic - ipca, 2)
    clima = "INVERNO MACRO" if juro_real > 10 else "VERAO MACRO"
    return dict(selic=selic, ipca=ipca, ntnb=ntnb, copom_min=copom_min,
                juro_real=juro_real, clima=clima, src_s=src_s, src_i=src_i,
                now=now, erros=erros)

@st.cache_data(ttl=300)
def fetch_preco(ticker):
    if not YF_OK or not ticker:
        return None, "yfinance indisponivel"
    try:
        sufixo = "" if ticker.endswith(".SA") else ".SA"
        t = yf.Ticker(ticker + sufixo)
        h = t.history(period="1d")
        if h.empty:
            return None, "Sem dados"
        return round(float(h["Close"].iloc[-1]), 2), f"yFinance [{datetime.now().strftime('%d/%m %H:%M')}]"
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════════════════════
# PARSE DE LIQUIDEZ - CORRIGIDO PARA MILHOES/BILHOES
# Exemplos aceitos:
#   "R$ 557,42 Milhoes"  -> 557_420_000
#   "1,2 Bilhoes"        -> 1_200_000_000
#   "500k"               -> 500_000
#   "1.500.000"          -> 1_500_000
# ═══════════════════════════════════════════════════════════════════════════
def parse_liquidez(raw):
    """
    Converte string de liquidez para float em R$ absolutos.
    Casos criticos (Investidor10):
      'R$ 557,42 Milhoes'  -> 557_420_000 (NAO 557!)
      '1,2 Bilhoes'        -> 1_200_000_000
      '500k' / '500K'      -> 500_000
      '1.500.000'          -> 1_500_000
      '250M' / '1.2B'      -> sufixo unitario
    """
    if not raw: return None
    s = raw.strip()
    s = re.sub(r"[Rr]\$\s*", "", s).strip()
    su = s.upper()
    mul = 1
    # Sufixos por extenso (prioridade maxima)
    if re.search(r"BILH", su):
        mul = 1_000_000_000
        s = re.sub(r"BILH[A-Za-z]*", "", s, flags=re.I).strip()
    elif re.search(r"MILH", su):
        mul = 1_000_000
        s = re.sub(r"MILH[A-Za-z]*", "", s, flags=re.I).strip()
    else:
        # Sufixo unitario no final: 500k, 250M, 1.2B
        m_suf = re.search(r"([KkMmBb])\s*$", s)
        if m_suf:
            c = m_suf.group(1).upper()
            if c == "K": mul = 1_000
            elif c == "M": mul = 1_000_000
            elif c == "B": mul = 1_000_000_000
            s = s[:m_suf.start()].strip()
    # Normaliza separadores numericos BR
    if re.search(r"\d\.\d{3}", s):
        if "," in s:
            s = s.replace(".", "").replace(",", ".")  # 1.234.567,89 -> 1234567.89
        else:
            s = s.replace(".", "")                    # 1.500.000 -> 1500000
    elif "," in s and "." not in s:
        s = s.replace(",", ".")                       # 557,42 -> 557.42
    s = re.sub(r"[^\d.\-]", "", s)
    if not s: return None
    try: return float(s) * mul
    except Exception: return None

def fmt_liquidez(val):
    if val is None:
        return "[DADO INDISPONIVEL NO FEED]"
    if val >= 1_000_000_000:
        return f"R$ {val/1e9:.2f} Bilhoes/dia"
    if val >= 1_000_000:
        return f"R$ {val/1e6:.2f} Milhoes/dia"
    if val >= 1_000:
        return f"R$ {val/1e3:.1f} mil/dia"
    return f"R$ {val:,.0f}/dia"

def avaliar_liquidez(val):
    if val is None:
        return "[DADO INDISPONIVEL NO FEED]", False
    if val >= 5_000_000:
        return f"OK LIQUIDEZ ADEQUADA ({fmt_liquidez(val)})", False
    if val >= 1_000_000:
        return f"LIQUIDEZ MODERADA - monitorar ({fmt_liquidez(val)})", False
    return f"AVA-2 RISCO LIQUIDEZ ({fmt_liquidez(val)} < R$1M)", True

# ═══════════════════════════════════════════════════════════════════════════
# PED - EXTRACAO AUTOMATICA DE DADOS DO TEXTO COLADO
# ═══════════════════════════════════════════════════════════════════════════
def _fnum(padrao, texto):
    m = re.search(padrao, texto, re.I | re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip()
    # Remove sufixos nao numericos, normaliza separadores
    if re.search(r"\d\.\d{3}", raw) and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    raw = re.sub(r"[^\d\.\-]", "", raw)
    try:
        return float(raw)
    except Exception:
        return None

def garimpar_ped(texto):
    t = texto.upper()
    d = {}
    d["lpa"]  = _fnum(r"LPA[\s\S]{0,50}?([-]?[\d]+[,.][\d]+)", t)
    d["vpa"]  = _fnum(r"VPA[\s\S]{0,50}?([\d]+[,.][\d]+)", t)
    m = re.search(r"(?:DIVIDEND\s*YIELD|DY)[\s\S]{0,40}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["dy"]   = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"ROE[\s\S]{0,40}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["roe"]  = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"D[IÍ]V[\s\S]{0,15}?EBITDA[\s\S]{0,30}?([\d]+[,.][\d]+)", t, re.I)
    if not m:
        m = re.search(r"D/EBITDA[\s\S]{0,20}?([\d]+[,.][\d]+)", t, re.I)
    d["d_ebitda"] = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"LTV[\s\S]{0,20}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["ltv"]  = float(m.group(1).replace(",", ".")) if m else None
    # Liquidez - captura valor + sufixo de magnitude
    m_liq = re.search(
        r"LIQUIDEZ\s+(?:M[EÉ]DIA\s+)?DI[AÁ]RIA[\s\S]{0,80}?"
        r"(R?\$?\s*[\d]+[,.][\d]+(?:[,.][\d]+)?\s*(?:MILH[OÕ]ES?|BILH[OÕ]ES?|[MBK])?)",
        t, re.I)
    if m_liq:
        d["liquidez_raw"] = m_liq.group(1).strip()
        d["liquidez"] = parse_liquidez(d["liquidez_raw"])
    else:
        d["liquidez"] = None
        d["liquidez_raw"] = None
    m = re.search(r"CAGR[\s\S]{0,30}?(?:DPA|DIVIDENDO|PROVENTO)[\s\S]{0,20}?([\d]+[,.][\d]+)\s*%", t, re.I)
    if not m:
        m = re.search(r"(?:DPA|PROVENTO)[\s\S]{0,10}?CAGR[\s\S]{0,20}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["cagr_dpa"] = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"VAC[AÂ]NCIA[\s\S]{0,30}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["vacancia"] = float(m.group(1).replace(",", ".")) if m else None
    m = re.search(r"INADIMPL[EÊ]NCIA[\s\S]{0,30}?([\d]+[,.][\d]+)\s*%", t, re.I)
    d["inadimplencia"] = float(m.group(1).replace(",", ".")) if m else None
    # Historico LPA
    anos = re.findall(r"LPA[\s\S]{0,5}?(\d{4})[\s\S]{0,15}?([-]?[\d]+[,.][\d]+)", t, re.I)
    lpa_hist = {}
    for ano, val in anos:
        try:
            lpa_hist[int(ano)] = float(val.replace(",", "."))
        except Exception:
            pass
    d["lpa_historico"] = dict(sorted(lpa_hist.items(), reverse=True))
    return d

# ═══════════════════════════════════════════════════════════════════════════
# PARSER DE CARTEIRA - aceita texto livre colado (Investidor10, StatusInvest)
# ═══════════════════════════════════════════════════════════════════════════
TICKER_RE = re.compile(r"\b([A-Z]{4}\d{1,2})\b")

def parsear_carteira(texto):
    """
    Extrai ativos de texto livre.
    1. Busca linhas com ticker + percentual
    2. Fallback: todos os tickers encontrados com pct igual
    3. Para cada ticker, garimpa dados do contexto ao redor
    """
    ativos = []
    linhas = texto.split("\n")
    # Tentativa 1: ticker + % na mesma linha
    for linha in linhas:
        tks = TICKER_RE.findall(linha.upper())
        pcts = re.findall(r"([\d]+[,.][\d]+)\s*%", linha)
        if tks and pcts:
            pct = float(pcts[0].replace(",", "."))
            if 0.01 <= pct <= 100:
                ativos.append({"ticker": tks[0], "pct": pct})
    # Tentativa 2: so tickers, pct igual
    if not ativos:
        tks_todos = list(dict.fromkeys(TICKER_RE.findall(texto.upper())))
        if tks_todos:
            pct_ig = round(100 / len(tks_todos), 2)
            for tk in tks_todos:
                ativos.append({"ticker": tk, "pct": pct_ig})
    if not ativos:
        return []
    # Dividir texto por blocos de ticker para extracao contextual
    blocos = {}
    partes = re.split(r"\b([A-Z]{4}\d{1,2})\b", texto.upper())
    i = 0
    while i < len(partes):
        if re.match(r"^[A-Z]{4}\d{1,2}$", partes[i].strip()):
            tk = partes[i].strip()
            bloco = partes[i] + (partes[i+1] if i+1 < len(partes) else "")
            blocos[tk] = bloco
        i += 1

    resultado = []
    for a in ativos:
        tk = a["ticker"]
        bloco_ativo = blocos.get(tk, texto)
        dados = garimpar_ped(bloco_ativo)
        # Detecta FII pelo sufixo 11
        tipo_hint = "FII TIJOLO" if re.match(r"[A-Z]{4}11$", tk) else "ACOES"
        resultado.append({
            "ticker": tk,
            "pct": a["pct"],
            "tipo": tipo_hint,
            "setor": "",
            "preco": None,
            **{k: dados.get(k) for k in (
                "lpa","vpa","dy","roe","d_ebitda","ltv",
                "liquidez","liquidez_raw","cagr_dpa","vacancia",
                "inadimplencia","lpa_historico")},
        })
    return resultado

# ═══════════════════════════════════════════════════════════════════════════
# TENDENCIA DE LUCROS
# ═══════════════════════════════════════════════════════════════════════════
def tendencia(hist):
    if len(hist) < 3:
        return "[DADO INDISPONIVEL NO FEED]"
    v = list(hist.values())[:3]
    a1, a2, a3 = v
    if any(x < 0 for x in v):
        return "Prejuizo Recorrente AVA-1"
    if a1 > a2 > a3:
        return "Crescente OK"
    if a1 < a2 < a3:
        return "Decrescente 3 anos AVA-1"
    mx = max(abs((a1-a2)/a2), abs((a2-a3)/a3))*100 if a2 and a3 else 100
    return "Estavel" if mx <= 10 else "Irregular"

# ═══════════════════════════════════════════════════════════════════════════
# SCORECARD - MODULO 8 PATCH 7
# ═══════════════════════════════════════════════════════════════════════════
def pilar_R(cagr):
    if cagr is None: return 10, "CAGR indisponivel -> neutro"
    if cagr > 10:    return 20, f"CAGR {cagr:.1f}% Frutos Acelerados OK"
    if cagr > 5:     return 15, f"CAGR {cagr:.1f}% Frutos Crescentes"
    if cagr > 0:     return 10, f"CAGR {cagr:.1f}% Frutos Estaveis"
    return 5, f"CAGR {cagr:.1f}% Estagnado"

_SET = {
    20: ["transmissao","transmiss","saneamento","banco","seguro","saude","financei"],
    15: ["eletric","energia","geracao","distribui","telecom","alimentar","agua"],
    10: ["logist","industria","transport","carga"],
    5:  ["mineracao","siderurg","petroleo","construcao","varejo","commodit","papel","celulose"],
}
_FII = {
    20: ["logist","saude","agencia","educac","hospital"],
    15: ["shopping","laje","corporat","cri essencial"],
    10: ["cri","papel","recebiv"],
    5:  ["hotel","residencial"],
}

def pilar_E(setor, tipo):
    s = re.sub(r"[^a-z]", "", setor.lower())
    mapa = _FII if "FII" in tipo.upper() else _SET
    for pts, kws in mapa.items():
        if any(k in s for k in kws):
            return pts, setor
    return 10, f"{setor or 'ND'} - classificar manualmente"

def pilar_N(roe, vac, iad, tipo, liq_small, d_ebitda, cagr, tend_str):
    ctx = ""
    if tipo == "ACOES" or tipo == "ACOES":
        if roe is None: return None, "[DADO INDISPONIVEL NO FEED]", ctx
        if liq_small and d_ebitda and d_ebitda < 1.5 and cagr and cagr > 5 and "Crescente" in tend_str:
            ctx = f"CONTEXTO SMALL CAP: ROE {roe:.1f}% pode refletir reinvestimento."
        if roe > 20:  return 20, f"ROE {roe:.1f}% Fosso Economico OK", ctx
        if roe >= 15: return 15, f"ROE {roe:.1f}% Gestao Muito Eficaz", ctx
        if roe >= 10: return 10, f"ROE {roe:.1f}% Gestao Eficaz", ctx
        return 5, f"ROE {roe:.1f}% Gestao Abaixo", ctx
    elif "TIJOLO" in tipo.upper():
        if vac is None: return None, "[DADO INDISPONIVEL NO FEED]", ctx
        if vac < 5:   return 20, f"Vacancia {vac:.1f}% Premium OK", ctx
        if vac <= 10: return 15, f"Vacancia {vac:.1f}% Boa Ocupacao", ctx
        if vac <= 15: return 10, f"Vacancia {vac:.1f}% Moderada", ctx
        return 5, f"Vacancia {vac:.1f}% Risco Elevado", ctx
    else:  # PAPEL
        if iad is None: return None, "[DADO INDISPONIVEL NO FEED]", ctx
        if iad < 1:   return 20, f"Inadimp {iad:.1f}% Premium OK", ctx
        if iad <= 3:  return 15, f"Inadimp {iad:.1f}% Moderado", ctx
        if iad <= 5:  return 10, f"Inadimp {iad:.1f}% Atencao", ctx
        return 5, f"Inadimp {iad:.1f}% Risco Elevado", ctx

def pilar_A_acoes(lpa, vpa, preco):
    if not lpa or not vpa or lpa <= 0 or vpa <= 0:
        return 5, "LPA/VPA negativo ou ausente - Graham NA", None
    if not preco:
        return 5, "Preco indisponivel", None
    vi = round(math.sqrt(22.5 * lpa * vpa), 2)
    mg = round(((vi - preco) / vi) * 100, 2)
    if mg > 20:    return 20, f"Margem {mg:.1f}% Grande Desconto OK  VI=R${vi:.2f}", vi
    if mg > 0:     return 15, f"Margem {mg:.1f}% Pequeno Desconto  VI=R${vi:.2f}", vi
    if mg >= -20:  return 10, f"Margem {mg:.1f}% Leve Premio  VI=R${vi:.2f}", vi
    return 5, f"Margem {mg:.1f}% Premio Elevado  VI=R${vi:.2f}", vi

def pilar_A_tijolo(preco, vpa):
    if not preco or not vpa or vpa == 0: return None, "[DADO INDISPONIVEL NO FEED]"
    pvp = round(preco / vpa, 2)
    if pvp <= 0.90: return 20, f"P/VP {pvp:.2f} Grande Desconto OK"
    if pvp <= 1.00: return 15, f"P/VP {pvp:.2f} Proximo do Justo"
    if pvp <= 1.10: return 10, f"P/VP {pvp:.2f} Leve Premio"
    return 5, f"P/VP {pvp:.2f} Premio Elevado"

def pilar_A_papel(dy, ntnb, clima):
    if dy is None or ntnb is None: return None, "[DADO INDISPONIVEL NO FEED]"
    spread = round(dy - ntnb, 2)
    suf = " (Inverno - spread pressionado)" if "INVERNO" in clima.upper() else ""
    if spread > 4.0:  return 20, f"Spread {spread:.2f}pp Premio Elevado OK{suf}"
    if spread >= 2.0: return 15, f"Spread {spread:.2f}pp Premio Adequado{suf}"
    if spread > 0:    return 10, f"Spread {spread:.2f}pp Premio Baixo{suf}"
    return 5, f"Spread {spread:.2f}pp Sem Premio{suf}"

def score100(notas):
    v = [n for n in notas if n is not None]
    if not v: return 0.0, 0
    return round(sum(v)/(len(v)*20)*100, 1), len(v)*20

def diag_score(sc):
    if sc < 40: return "TERRENO ARIDO: Fundamentos criticos. (Cap. 11.7)"
    if sc < 60: return "SOLO EM RECUPERACAO: Abaixo do limiar minimo (60)."
    if sc < 75: return "SOLO FERTIL: Base razoavel com gaps."
    if sc < 85: return "ARVORE SAUDAVEL: Fundamentos solidos."
    return "SAFRA RESILIENTE: Alta robustez. Acima do limiar do livro."

def nat(setor, tipo):
    if "PAPEL" in tipo.upper(): return "Papel"
    if "TIJOLO" in tipo.upper(): return "Tijolo"
    s = setor.lower()
    ciclicos = ["minerac","siderurg","petroleo","construcao","varejo","commodit"]
    defensiv = ["banco","seguro","saneamento","energia","eletric","saude","aliment","telecom"]
    if any(p in s for p in ciclicos): return "Ciclica"
    if any(p in s for p in defensiv): return "Defensiva"
    return "Semi-Ess"

def gerar_pdf(txt):
    if not FPDF_OK: return b""
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Courier", size=8)
    for linha in txt.split("\n"):
        pdf.cell(0, 4, txt=linha.encode("latin-1","ignore").decode("latin-1"), ln=1)
    return bytes(pdf.output())

def fmt_ancora(m, copom):
    ok = "OK" if copom >= m["copom_min"] else "OBSOLETO"
    return f"""\
+---------------+-----------+------------------+--------------+------------------+
| Variavel      | Valor     | Fonte            | Data/Hora    | Prova Sombra     |
+---------------+-----------+------------------+--------------+------------------+
| Selic Meta    | {m['selic']:>7.2f}%  | {m['src_s']:<16} | {m['now']:<12} | COPOM {copom} {ok} |
| IPCA 12m      | {m['ipca']:>7.2f}%  | {m['src_i']:<16} | {m['now']:<12} | [Mes recente]    |
| NTN-B Longa   |IPCA+{m['ntnb']:.2f}% | Backup Python    | {m['now']:<12} | [Regra D-1]      |
| Juro Real     | {m['juro_real']:>7.2f}%  | Calculado        | Selic-IPCA   | {m['clima'][:16]:<16} |
+---------------+-----------+------------------+--------------+------------------+"""

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
st.code(AVISO_LEGAL, language="text")
st.title("Sistema de Ensino R.E.N.D.A. V.102.09 FULL")
st.caption("Apendice Digital - Metodo R.E.N.D.A. de Investimentos - Laerson Endrigo Ely, 2026")

with st.sidebar:
    st.markdown("### Painel de Controle")
    if st.button("Sair"):
        st.session_state["authenticated"] = False; st.rerun()
    st.markdown("---")
    st.markdown("**V.102.09 FULL** | Modulos A + C")
    st.markdown("**Liquidez:** Patch Milhoes/Bilhoes OK")

# ANCORA MACRO
st.subheader("ETAPA G5 - Ancora de Dados Macro")
macro = fetch_macro()
if macro["erros"]:
    st.warning("Fallback ativado: " + " | ".join(macro["erros"]))
c1, c2, c3, c4 = st.columns(4)
s_ui  = c1.number_input("Selic Meta (%)",       value=macro["selic"], step=0.25, format="%.2f")
i_ui  = c2.number_input("IPCA 12m (%)",         value=macro["ipca"],  step=0.10, format="%.2f")
nb_ui = c3.number_input("NTN-B Longa (IPCA+%)", value=macro["ntnb"], step=0.10, format="%.2f")
cp_ui = c4.number_input("No Reuniao COPOM",      value=int(macro["copom_min"]), step=1)

if int(cp_ui) < macro["copom_min"]:
    st.error(f"COPOM {int(cp_ui)} < minimo {macro['copom_min']}. Insira dado atual."); st.stop()

MA = {**macro, "selic": s_ui, "ipca": i_ui, "ntnb": nb_ui,
      "juro_real": round(s_ui - i_ui, 2),
      "clima": "INVERNO MACRO" if (s_ui - i_ui) > 10 else "VERAO MACRO"}
st.code(fmt_ancora(MA, int(cp_ui)), language="text")
st.markdown("---")

aba_a, aba_c = st.tabs(["Modulo A - Ticker Unico", "Modulo C - Visao do Bosque (Carteira)"])

# ═══════════════════════════════════════════════════════════════════════════
# MODULO A
# ═══════════════════════════════════════════════════════════════════════════
with aba_a:
    st.subheader("Modulo A - Analise de Ativo Unico")
    ca1, ca2 = st.columns([2, 2])
    with ca1:
        ticker_a = st.text_input("Ticker:", value="", placeholder="Ex: TAEE11").upper().strip()
    with ca2:
        TIPOS = ["ACOES", "FII TIJOLO", "FII PAPEL"]
        tipo_a = st.selectbox("Trilha:", TIPOS)

    if ticker_a:
        setor_a = st.text_input("Setor / Segmento:", placeholder="Ex: Transmissao Eletrica")
        pyf_a, src_a = fetch_preco(ticker_a)
        cp_col1, cp_col2 = st.columns([2, 3])
        with cp_col1:
            preco_a = st.number_input("Cotacao R$ (Patch 8):", value=float(pyf_a or 0), step=0.01, format="%.2f")
        with cp_col2:
            st.info(f"**Auto:** {src_a}  \n**Capturado:** R$ {pyf_a:.2f}" if pyf_a else f"**Auto:** {src_a}  \nInforme manualmente.")
        preco_final = preco_a if preco_a > 0 else pyf_a

        st.markdown("#### Colagem PED - Investidor10 / StatusInvest")
        st.caption("Cole o texto da aba Indicadores. Liquidez e interpretada automaticamente com Milhoes/Bilhoes.")
        txt_a = st.text_area("Dados do ativo:", height=200,
            placeholder="Cole aqui os dados do Investidor10/StatusInvest.\nExemplo de linha de liquidez que funciona:\nLiquidez Media Diaria R$ 557,42 Milhoes\nLiquidez Media Diaria 1,2 Bilhoes\nLiquidez Media Diaria 500k")
        noticia_a = st.text_input("Titulo da noticia recente (Patch 5):")

        with st.expander("Insercao / Correcao Manual de Campos"):
            mf1, mf2, mf3, mf4 = st.columns(4)
            lpa_m  = mf1.number_input("LPA (R$)",      value=0.0, step=0.01, format="%.4f", key="al_lpa")
            vpa_m  = mf1.number_input("VPA (R$)",      value=0.0, step=0.01, format="%.4f", key="al_vpa")
            dy_m   = mf2.number_input("DY (%)",        value=0.0, step=0.1,  format="%.2f", key="al_dy")
            roe_m  = mf2.number_input("ROE (%)",       value=0.0, step=0.1,  format="%.2f", key="al_roe")
            de_m   = mf3.number_input("D/EBITDA (x)",  value=0.0, step=0.1,  format="%.2f", key="al_de")
            ltv_m  = mf3.number_input("LTV (%)",       value=0.0, step=0.1,  format="%.2f", key="al_ltv")
            cagr_m = mf4.number_input("CAGR DPA (%)",  value=0.0, step=0.1,  format="%.2f", key="al_cagr")
            liq_str_m = mf4.text_input("Liquidez Diaria (ex: 557,42 Milhoes):", key="al_liq")
            vac_m  = mf1.number_input("Vacancia (%)",  value=0.0, step=0.1,  format="%.2f", key="al_vac")
            iad_m  = mf2.number_input("Inadimp. (%)",  value=0.0, step=0.1,  format="%.2f", key="al_iad")

        if st.button("Executar FASE 2 - Scorecard R.E.N.D.A.", type="primary", use_container_width=True, key="btn_a"):
            ped = garimpar_ped(txt_a) if txt_a else {}

            def pck(mv, k): return mv if mv and mv != 0.0 else ped.get(k)
            lpa      = pck(lpa_m, "lpa")
            vpa      = pck(vpa_m, "vpa")
            dy       = pck(dy_m, "dy")
            roe      = pck(roe_m, "roe")
            d_ebitda = pck(de_m, "d_ebitda")
            ltv      = pck(ltv_m, "ltv")
            cagr_dpa = pck(cagr_m, "cagr_dpa")
            liquidez = parse_liquidez(liq_str_m) if liq_str_m else ped.get("liquidez")
            liq_raw  = liq_str_m or ped.get("liquidez_raw", "")
            vacancia = pck(vac_m, "vacancia")
            inadimp  = pck(iad_m, "inadimplencia")
            lpa_hist = ped.get("lpa_historico", {})
            tend_str = tendencia(lpa_hist) if lpa_hist else "[DADO INDISPONIVEL NO FEED]"
            liq_diag, liq_ava2 = avaliar_liquidez(liquidez)
            liq_fmt_s = f"{fmt_liquidez(liquidez)}"
            if liq_raw:
                liq_fmt_s += f" (bruto: {liq_raw})"

            # GATE
            st.markdown("#### FASE 1 - Gate de Auditoria")
            def fc(nome, val):
                v = str(val) if val is not None else "[DADO INDISPONIVEL NO FEED]"
                return f"| {nome:<40} | {v:<38} |"

            gate = f"""\
+------------------------------------------+----------------------------------------+
| Campo                                    | Valor                                  |
+------------------------------------------+----------------------------------------+
{fc('Campo 1 - LPA (R$)', lpa)}
{fc('Campo 2 - VPA (R$)', vpa)}
{fc('Campo 3 - DY (%)', f'{dy}%' if dy else None)}
{fc('Campo 4 - ROE (%)', f'{roe}%' if roe else None)}
{fc('Campo 5 - D/EBITDA (x)', f'{d_ebitda}x' if d_ebitda else None)}
{fc('Campo 5 - LTV (%) - FII Tijolo', f'{ltv}%' if ltv else None)}
{fc('Campo 6 - Liquidez Diaria', liq_fmt_s)}
{fc('Campo 7 - CAGR DPA (%)', f'{cagr_dpa}%' if cagr_dpa else None)}
{fc('Campo 8 - Cotacao R$', preco_final)}
{fc('Campo 9A - Vacancia (%)', f'{vacancia}%' if vacancia else None)}
{fc('Campo 9B - Inadimplencia (%)', f'{inadimp}%' if inadimp else None)}
{fc('Campo 9C - Tendencia Lucros 3a', tend_str)}
+------------------------------------------+----------------------------------------+
| Patch 5 - Noticia Sombra                 | {'OK: '+noticia_a[:35] if noticia_a else 'NAO INFORMADO':<38} |
| Patch 8 - Preco Sincronizado             | {'OK: R$ '+str(preco_final) if preco_final else 'MANUAL':<38} |
| Liquidez Interpretada                    | {liq_diag[:38]:<38} |
+------------------------------------------+----------------------------------------+"""
            st.code(gate, language="text")

            # SCORECARD
            st.markdown("#### FASE 2 - Scorecard R.E.N.D.A.")
            r_n, r_d = pilar_R(cagr_dpa)
            e_n, e_d = pilar_E(setor_a or "ND", tipo_a)
            n_n, n_d, n_ctx = pilar_N(roe, vacancia, inadimp, tipo_a,
                                      liq_ava2, d_ebitda, cagr_dpa, tend_str)
            vi_a = None
            if tipo_a == "ACOES":
                a_n, a_d, vi_a = pilar_A_acoes(lpa, vpa, preco_final)
            elif tipo_a == "FII TIJOLO":
                a_n, a_d = pilar_A_tijolo(preco_final, vpa)
            else:
                a_n, a_d = pilar_A_papel(dy, nb_ui, MA["clima"])

            sc, pp = score100([r_n, e_n, n_n, a_n])

            def sl(p, c, n, d):
                ns = f"{n}/20" if n is not None else " N/A"
                return f"| {p:<6} | {c:<26} | {ns:>6} | {d[:54]:<54} |"

            soma_b = sum(x for x in [r_n,e_n,n_n,a_n] if x is not None)
            sc_txt = f"""\
+--------+----------------------------+--------+--------------------------------------------------------+
| Pilar  | Criterio (Trilha)          | Nota   | Diagnostico                                            |
+--------+----------------------------+--------+--------------------------------------------------------+
{sl('R', 'CAGR DPA 3 anos', r_n, r_d)}
{sl('E', 'Setor / Segmento', e_n, e_d)}
{sl('N', 'ROE/Vac/Inadimp.', n_n, n_d)}
{sl('D', 'Desvio Talmud', None, '(Modulo C - carteira)')}
{sl('A', tipo_a[:26], a_n, a_d)}
+--------+----------------------------+--------+--------------------------------------------------------+
| SUBTOT | Soma bruta                 | {soma_b:>3}/{pp:<3}  |                                                        |
| SCORE  | Base 100                   | {sc:>5}/100|                                                        |
+--------+----------------------------+--------+--------------------------------------------------------+
{diag_score(sc)}"""
            st.code(sc_txt, language="text")
            st.progress(int(sc) / 100)
            if n_ctx:
                st.markdown(f'<div class="warn-box">{n_ctx}</div>', unsafe_allow_html=True)

            # AVA
            st.markdown("#### FASE 3 - Protocolo AVA")
            avas = []
            if "AVA-1" in tend_str:
                avas.append(f"AVA-1: {tend_str} - Veto imediato. (Cap. 11.7)")
            if d_ebitda and d_ebitda > 4:
                avas.append(f"AVA-2 RUINA: D/EBITDA {d_ebitda:.1f}x > 4x. (Cap. 11.7)")
            elif d_ebitda and d_ebitda > 3:
                avas.append(f"AVA-2 ATENCAO: D/EBITDA {d_ebitda:.1f}x > 3x.")
            if ltv and ltv > 25:
                avas.append(f"AVA-2 LTV: {ltv:.1f}% > 25%. (Cap. 11.7)")
            if liq_ava2:
                avas.append(f"AVA-2 LIQUIDEZ: {fmt_liquidez(liquidez)} < R$1M/dia.")

            if tipo_a == "ACOES" and roe is not None:
                sp_ke = round(roe - s_ui, 2)
                if sp_ke >= 0:
                    st.markdown(f'<div class="ok-box">OK Geracao de Valor: ROE {roe:.1f}% > Ke {s_ui:.1f}%. Spread: +{sp_ke:.1f}% (Cap. 6.1)</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="warn-box">Teste Acido: ROE {roe:.1f}% &lt; Ke {s_ui:.1f}%. Spread: {sp_ke:.1f}%. Verificar Campo 9C. (Cap. 6.1)</div>', unsafe_allow_html=True)

            for ava in avas:
                st.markdown(f'<div class="ava-alert">{ava}</div>', unsafe_allow_html=True)
            if not avas:
                st.markdown('<div class="ok-box">OK - Nenhum AVA acionado nesta analise.</div>', unsafe_allow_html=True)

            if tipo_a == "ACOES" and vi_a and preco_final:
                mg_g = round(((vi_a - preco_final) / vi_a) * 100, 2)
                st.markdown("#### Radar Graham (Cap. 6.5)")
                st.code(f"""\
Formula   | VI = raiz(22,5 x LPA x VPA)
Substitui | VI = raiz(22,5 x {lpa:.4f} x {vpa:.4f})
Resultado | R$ {vi_a:.2f}

Margem    | ((VI - Preco) / VI) x 100
Substitui | (({vi_a:.2f} - {preco_final:.2f}) / {vi_a:.2f}) x 100
Resultado | {mg_g:.2f}%

{'OK MARGEM PRESENTE.' if mg_g > 0 else 'AUSENCIA DE MARGEM - preco acima do VI teorico.'}
Referencia teorica - calibrado EUA anos 1970. (Cap. 6.5 / 6.7.3)""", language="text")

            st.code(RODAPE, language="text")
            if FPDF_OK:
                pdf_a = gerar_pdf(AVISO_LEGAL+"\n"+fmt_ancora(MA,int(cp_ui))+"\n"+gate+"\n"+sc_txt+"\n"+RODAPE)
                st.download_button("Baixar Relatorio PDF", pdf_a,
                    f"RENDA_{ticker_a}_{date.today()}.pdf", "application/pdf", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# MODULO C - VISAO DO BOSQUE
# ═══════════════════════════════════════════════════════════════════════════
with aba_c:
    st.subheader("Modulo C - Visao do Bosque (Carteira)")

    st.markdown("""
<div class="info-box">
<b>NOVO: Cole a carteira completa diretamente!</b><br>
Aceita texto exportado do <b>Investidor10</b>, <b>StatusInvest</b>, planilha Excel, ou qualquer
consolidado com tickers brasileiros (TAEE11, ITUB4...) e percentuais opcionais.<br>
Liquidez interpretada corretamente: <b>Milhoes, Bilhoes, k</b> (ex: R$ 557,42 Milhoes = R$ 557.420.000)
</div>""", unsafe_allow_html=True)

    modo = st.radio("Modo de entrada:",
                    ["Colar texto da carteira (automatico)", "Preencher ativo por ativo (manual)"],
                    horizontal=True)
    aporte = st.number_input("Aporte Mensal R$ (Simulador Grande Virada):", min_value=0.0, value=1000.0, step=100.0)

    ativos_c = []

    # MODO COLAGEM
    if "automatico" in modo:
        st.markdown("#### Cole o texto completo da sua carteira")
        st.caption("Formatos aceitos: exportacao Investidor10, StatusInvest, planilha, lista de tickers com ou sem percentuais.")
        txt_cart = st.text_area("Texto da carteira:", height=300,
            placeholder="""Exemplos de formatos aceitos:

--- Formato com percentuais ---
TAEE11  5,5%   Transmissao Eletrica  LPA 1,23  VPA 8,45  DY 8,2%  ROE 14%  Liquidez Media Diaria R$ 557,42 Milhoes
MXRF11  8,0%   FII Papel             VPA 10,12  DY 13,5%  Inadimplencia 0,8%  Liquidez Media Diaria R$ 80 Milhoes
ITUB4  12,0%   Banco                 LPA 3,45  VPA 18,20  DY 4,2%  ROE 21%  Liquidez Media Diaria R$ 2,3 Bilhoes

--- Apenas tickers (distribuicao igual automatica) ---
TAEE11 MXRF11 ITUB4 BBAS3 HGLG11

--- Exportacao bruta do Investidor10 / StatusInvest ---
Cole o texto completo. O sistema detecta os tickers e extrai os dados automaticamente.""")

        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("Detectar Ativos Automaticamente", use_container_width=True) and txt_cart:
            detectados = parsear_carteira(txt_cart)
            if detectados:
                st.session_state["ativos_detectados"] = detectados
                st.success(f"OK: {len(detectados)} ativo(s) detectado(s): {', '.join(a['ticker'] for a in detectados)}")
            else:
                st.error("Nenhum ticker detectado. Verifique o formato (ex: TAEE11, ITUB4).")

        if col_btn2.button("Limpar Deteccao", use_container_width=True):
            if "ativos_detectados" in st.session_state:
                del st.session_state["ativos_detectados"]

        if "ativos_detectados" in st.session_state:
            det = st.session_state["ativos_detectados"]
            st.markdown(f"#### Revise os {len(det)} ativo(s) detectado(s)")
            st.caption("Corrija tipo, setor, percentuais e campos de dados. Liquidez: informe como aparece na plataforma (ex: 557,42 Milhoes).")

            for idx, a in enumerate(det):
                campos_ok = sum(1 for k in ["dy","roe","lpa","vpa","cagr_dpa","vacancia","inadimplencia"] if a.get(k))
                icone = "OK" if campos_ok >= 2 else "!"
                with st.expander(f"[{icone}] {a['ticker']} - {a['pct']:.1f}% ({campos_ok}/7 campos extraidos)", expanded=False):
                    ec1, ec2, ec3, ec4 = st.columns([2,1,2,2])
                    a["ticker"] = ec1.text_input("Ticker", value=a["ticker"], key=f"ct_{idx}").upper().strip()
                    a["pct"]    = ec2.number_input("% Cart.", value=float(a["pct"]), step=0.5, format="%.1f", key=f"cp_{idx}")
                    TIPOS_C = ["ACOES", "FII TIJOLO", "FII PAPEL"]
                    tipo_idx = 0
                    if a.get("tipo","ACOES") in TIPOS_C:
                        tipo_idx = TIPOS_C.index(a["tipo"])
                    a["tipo"]   = ec3.selectbox("Tipo", TIPOS_C, index=tipo_idx, key=f"ctp_{idx}")
                    a["setor"]  = ec4.text_input("Setor", value=a.get("setor",""), key=f"cs_{idx}")

                    ef1, ef2, ef3, ef4 = st.columns(4)
                    v_lpa  = float(a.get("lpa") or 0)
                    v_vpa  = float(a.get("vpa") or 0)
                    v_dy   = float(a.get("dy") or 0)
                    v_roe  = float(a.get("roe") or 0)
                    v_de   = float(a.get("d_ebitda") or 0)
                    v_cagr = float(a.get("cagr_dpa") or 0)
                    v_vac  = float(a.get("vacancia") or 0)
                    v_iad  = float(a.get("inadimplencia") or 0)

                    nlpa  = ef1.number_input("LPA (R$)",       value=v_lpa,  step=0.0001, format="%.4f", key=f"clpa_{idx}")
                    nvpa  = ef1.number_input("VPA (R$)",       value=v_vpa,  step=0.0001, format="%.4f", key=f"cvpa_{idx}")
                    ndy   = ef2.number_input("DY (%)",         value=v_dy,   step=0.1,    format="%.2f", key=f"cdy_{idx}")
                    nroe  = ef2.number_input("ROE (%)",        value=v_roe,  step=0.1,    format="%.2f", key=f"croe_{idx}")
                    nde   = ef3.number_input("D/EBITDA (x)",  value=v_de,   step=0.1,    format="%.2f", key=f"cde_{idx}")
                    ncagr = ef3.number_input("CAGR DPA (%)",  value=v_cagr, step=0.1,    format="%.2f", key=f"ccagr_{idx}")
                    nvac  = ef4.number_input("Vacancia (%)",  value=v_vac,  step=0.1,    format="%.2f", key=f"cvac_{idx}")
                    niad  = ef4.number_input("Inadimp. (%)",  value=v_iad,  step=0.1,    format="%.2f", key=f"ciad_{idx}")

                    a["lpa"]  = nlpa if nlpa else a.get("lpa")
                    a["vpa"]  = nvpa if nvpa else a.get("vpa")
                    a["dy"]   = ndy  if ndy  else a.get("dy")
                    a["roe"]  = nroe if nroe else a.get("roe")
                    a["d_ebitda"] = nde   if nde   else a.get("d_ebitda")
                    a["cagr_dpa"] = ncagr if ncagr else a.get("cagr_dpa")
                    a["vacancia"] = nvac  if nvac  else a.get("vacancia")
                    a["inadimplencia"] = niad if niad else a.get("inadimplencia")

                    liq_field = st.text_input(
                        "Liquidez Diaria (informe como esta na plataforma):",
                        value=a.get("liquidez_raw") or "",
                        key=f"cliq_{idx}",
                        help="Ex: 557,42 Milhoes | 1,2 Bilhoes | 500k | 1500000")
                    if liq_field:
                        a["liquidez"] = parse_liquidez(liq_field)
                        a["liquidez_raw"] = liq_field

                    p_yf, _ = fetch_preco(a["ticker"])
                    v_preco = float(p_yf or a.get("preco") or 0)
                    a["preco"] = st.number_input("Cotacao R$ (Patch 8):", value=v_preco, step=0.01, format="%.2f", key=f"cpreco_{idx}") or p_yf

            ativos_c = st.session_state["ativos_detectados"]

    # MODO MANUAL
    else:
        n_at = st.number_input("No de ativos:", min_value=2, max_value=20, value=4)
        for idx in range(int(n_at)):
            with st.expander(f"Ativo {idx+1}", expanded=(idx < 2)):
                mc1, mc2, mc3, mc4 = st.columns([2,1,2,2])
                tk_m  = mc1.text_input("Ticker", key=f"mt_{idx}", placeholder="TAEE11").upper().strip()
                pct_m = mc2.number_input("% Cart.", min_value=0.0, max_value=100.0, step=5.0, key=f"mpct_{idx}")
                TIPOS_M = ["ACOES", "FII TIJOLO", "FII PAPEL"]
                tp_m  = mc3.selectbox("Tipo", TIPOS_M, key=f"mtp_{idx}")
                st_m  = mc4.text_input("Setor", key=f"mst_{idx}")

                mf1, mf2, mf3, mf4 = st.columns(4)
                lpa_mi  = mf1.number_input("LPA (R$)",     value=0.0, step=0.0001, format="%.4f", key=f"mlpa_{idx}")
                vpa_mi  = mf1.number_input("VPA (R$)",     value=0.0, step=0.0001, format="%.4f", key=f"mvpa_{idx}")
                dy_mi   = mf2.number_input("DY (%)",       value=0.0, step=0.1,    format="%.2f", key=f"mdy_{idx}")
                roe_mi  = mf2.number_input("ROE (%)",      value=0.0, step=0.1,    format="%.2f", key=f"mroe_{idx}")
                de_mi   = mf3.number_input("D/EBITDA (x)", value=0.0, step=0.1,    format="%.2f", key=f"mde_{idx}")
                cagr_mi = mf3.number_input("CAGR DPA (%)", value=0.0, step=0.1,    format="%.2f", key=f"mcagr_{idx}")
                vac_mi  = mf4.number_input("Vacancia (%)", value=0.0, step=0.1,    format="%.2f", key=f"mvac_{idx}")
                iad_mi  = mf4.number_input("Inadimp. (%)", value=0.0, step=0.1,    format="%.2f", key=f"miad_{idx}")
                liq_str_mi = st.text_input("Liquidez Diaria (ex: 557,42 Milhoes):", key=f"mliq_{idx}")
                p_yf_m, _ = fetch_preco(tk_m) if tk_m else (None,"")
                preco_mi = st.number_input("Cotacao R$ (Patch 8):", value=float(p_yf_m or 0), step=0.01, format="%.2f", key=f"mpreco_{idx}")

                if tk_m and pct_m > 0:
                    ativos_c.append({
                        "ticker": tk_m, "pct": pct_m, "tipo": tp_m, "setor": st_m,
                        "lpa": lpa_mi or None, "vpa": vpa_mi or None,
                        "dy": dy_mi or None,   "roe": roe_mi or None,
                        "d_ebitda": de_mi or None, "cagr_dpa": cagr_mi or None,
                        "vacancia": vac_mi or None, "inadimplencia": iad_mi or None,
                        "liquidez": parse_liquidez(liq_str_mi) if liq_str_mi else None,
                        "liquidez_raw": liq_str_mi or None,
                        "preco": preco_mi or p_yf_m,
                        "lpa_historico": {},
                    })

    # ANALISE
    pode = len(ativos_c) >= 2
    if not pode:
        st.info("Adicione pelo menos 2 ativos para executar a analise consolidada.")

    if pode and st.button("Executar Visao do Bosque - Modulo C", type="primary", use_container_width=True):
        total_pct = sum(a["pct"] for a in ativos_c)
        if abs(total_pct - 100) > 1.0:
            st.warning(f"Soma = {total_pct:.1f}%. Normalizando para 100%.")
            for a in ativos_c:
                a["pct"] = round(a["pct"] / total_pct * 100, 2)
        st.markdown("---")

        # C.0 Mapeamento
        st.markdown("### C.0 - Mapeamento da Carteira")
        mapa = "+---+----------+---------+----------+----------------------+----------+\n"
        mapa += "| # | Ticker   |   %     | Tipo     | Setor                | Natureza |\n"
        mapa += "+---+----------+---------+----------+----------------------+----------+\n"
        for idx, a in enumerate(ativos_c):
            nt = nat(a.get("setor",""), a["tipo"])
            a["natureza"] = nt
            ss = (a.get("setor") or "ND")[:20]
            mapa += f"| {idx+1:<1} | {a['ticker']:<8} | {a['pct']:>5.1f}%  | {a['tipo'][:8]:<8} | {ss:<20} | {nt:<8} |\n"
        mapa += "+---+----------+---------+----------+----------------------+----------+\n"
        mapa += "Classificacao indicativa. Verificar empresas multisetoriais.\n"
        st.code(mapa, language="text")

        # C.1 Talmud
        st.markdown("### C.1 - Termometro do Talmud (Pilar D)")
        pft = sum(a["pct"] for a in ativos_c if "FII" in a["tipo"].upper())
        pac = sum(a["pct"] for a in ativos_c if a["tipo"] == "ACOES")
        prf = max(0, 100 - pft - pac)
        df=abs(pft-33.33); da=abs(pac-33.33); dr=abs(prf-33.33)
        dm = round((df+da+dr)/3, 1)
        td, tn = (("POMAR EQUILIBRADO OK", 20) if dm<=5 else
                  ("DESEQUILIBRIO MODERADO", 10) if dm<=15 else ("MONOCULTURA Cap.7.3", 5))
        st.code(f"""\
+------------------+-------+--------+----------+
| Classe           | Atual | Alvo   | Desvio   |
+------------------+-------+--------+----------+
| FIIs             |{pft:>5.1f}% | 33,33% |{df:>5.1f} p.p|
| Acoes            |{pac:>5.1f}% | 33,33% |{da:>5.1f} p.p|
| RF/Reserva       |{prf:>5.1f}% | 33,33% |{dr:>5.1f} p.p|
+------------------+-------+--------+----------+
| Desvio Medio                  {dm:>5.1f} p.p|
| Diagnostico: {td}
+------------------------------------------+""", language="text")

        # C.2 Scorecard
        st.markdown("### C.2 - Scorecard Consolidado R.E.N.D.A.")
        sc_pond = 0.0
        rows = []
        for a in ativos_c:
            r_n, _ = pilar_R(a.get("cagr_dpa"))
            e_n, _ = pilar_E(a.get("setor","ND"), a["tipo"])
            n_n, _, _ = pilar_N(a.get("roe"), a.get("vacancia"), a.get("inadimplencia"),
                                 a["tipo"], False, a.get("d_ebitda"), a.get("cagr_dpa"),
                                 tendencia(a.get("lpa_historico",{})))
            if a["tipo"] == "ACOES":
                av_n, _, _ = pilar_A_acoes(a.get("lpa"), a.get("vpa"), a.get("preco"))
            elif a["tipo"] == "FII TIJOLO":
                av_n, _ = pilar_A_tijolo(a.get("preco"), a.get("vpa"))
            else:
                av_n, _ = pilar_A_papel(a.get("dy"), nb_ui, MA["clima"])
            sc_i, _ = score100([r_n, e_n, n_n, av_n])
            sc_pond += sc_i * (a["pct"] / 100)
            liq_d, liq_a2 = avaliar_liquidez(a.get("liquidez"))
            rows.append({"t": a["ticker"], "p": a["pct"],
                         "r": r_n, "e": e_n, "n": n_n, "d": tn, "a": av_n,
                         "sc": sc_i, "liq_ava2": liq_a2, "liq_fmt": fmt_liquidez(a.get("liquidez"))})
        sc_pond = round(sc_pond, 1)

        h = "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        h += "| Ticker   |   %  |  R  |  E  |  N  |  D  |  A  | Score |\n"
        h += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        for row in rows:
            def f(v): return f"{v:>3}" if v is not None else " --"
            h += f"| {row['t']:<8} |{row['p']:>4.0f}% | {f(row['r'])} | {f(row['e'])} | {f(row['n'])} | {f(row['d'])} | {f(row['a'])} | {row['sc']:>5.1f} |\n"
        h += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        h += f"| PONDERADO| 100% |                               | {sc_pond:>5.1f} |\n"
        h += "+----------+------+-----+-----+-----+-----+-----+-------+\n"
        h += diag_score(sc_pond)
        st.code(h, language="text")
        st.progress(int(sc_pond) / 100)

        # C.3 Grande Virada
        st.markdown("### C.3 - Simulador da Grande Virada")
        dy_pond = sum((a.get("dy") or 0)*(a["pct"]/100) for a in ativos_c)
        if dy_pond > 0 and aporte > 0:
            pat = round((aporte * 12) / (dy_pond / 100), 2)
            st.code(f"""\
DY Medio Ponderado = {dy_pond:.2f}%
Formula   | Pat_Virada = (Aporte x 12) / DY_decimal
Substitui | Pat_Virada = (R$ {aporte:,.2f} x 12) / {dy_pond/100:.4f}
Resultado | R$ {pat:,.2f}

Com R$ {pat:,.2f} em carteira, dividendos IGUALAM aporte anual.
Para SUPERAR (fator 1,2): R$ {pat*1.2:,.2f}
Projecao educacional. NAO constitui garantia. (Cap. 8.5.1)""", language="text")

        # C.4 Teste Acido
        c4_at = [a for a in ativos_c if a["tipo"]=="ACOES" and a.get("roe")]
        if c4_at:
            st.markdown("### C.4 - Teste Acido (ROE vs Ke)")
            c4 = "+----------+--------+--------+-------------------+\n| Ticker   | ROE %  | Ke %   | Spread/Diag.      |\n+----------+--------+--------+-------------------+\n"
            for a in c4_at:
                sp = round(a["roe"] - s_ui, 2)
                c4 += f"| {a['ticker']:<8} | {a['roe']:>5.1f}% | {s_ui:>5.1f}% | {('+' if sp>=0 else '')}{sp:+.2f}pp {'OK' if sp>=0 else 'ALERTA'} |\n"
            c4 += "+----------+--------+--------+-------------------+\n"
            st.code(c4, language="text")

        # C.5 Graham
        c5_at = [a for a in ativos_c if a["tipo"]=="ACOES" and a.get("lpa") and a["lpa"]>0 and a.get("vpa") and a["vpa"]>0]
        if c5_at:
            st.markdown("### C.5 - Radar Graham")
            c5 = "+----------+---------+---------+----------+----------+---------+\n| Ticker   | LPA     | VPA     | VI       | Preco    | Margem  |\n+----------+---------+---------+----------+----------+---------+\n"
            for a in c5_at:
                vi5 = round(math.sqrt(22.5*a["lpa"]*a["vpa"]), 2)
                mg5 = f"{((vi5-a['preco'])/vi5*100):+.1f}%" if a.get("preco") else "S/preco"
                c5 += f"| {a['ticker']:<8} | {a['lpa']:>7.4f} | {a['vpa']:>7.4f} | {vi5:>8.2f} | {(a.get('preco') or 0):>8.2f} | {mg5:<7} |\n"
            c5 += "+----------+---------+---------+----------+----------+---------+\n"
            st.code(c5, language="text")

        # C.6 Ciclicidade
        st.markdown("### C.6 - Matriz de Ciclicidade")
        pc = sum(a["pct"] for a in ativos_c if a.get("natureza")=="Ciclica")
        pd2 = sum(a["pct"] for a in ativos_c if a.get("natureza")=="Defensiva")
        po = 100-pc-pd2
        c6d = ("FLORESTA RESILIENTE" if pc<=30 else "FLORESTA MISTA" if pc<=50 else "ALERTA VOLATILIDADE EXTREMA")
        st.code(f"""\
+---------------------+-------+
| Natureza            |   %   |
+---------------------+-------+
| Ciclica             |{pc:>5.1f}% |
| Defensiva/Essencial |{pd2:>5.1f}% |
| FII/Semi-Essencial  |{po:>5.1f}% |
+---------------------+-------+
{c6d}""", language="text")

        # C.7 D/EBITDA
        c7_at = [a for a in ativos_c if a["tipo"]=="ACOES" and a.get("d_ebitda")]
        if c7_at:
            st.markdown("### C.7 - Asfixia Financeira (D/EBITDA)")
            c7 = "+----------+-----------+-------------------------------+\n| Ticker   | D/EBITDA  | Diagnostico                   |\n+----------+-----------+-------------------------------+\n"
            for a in c7_at:
                de = a["d_ebitda"]
                d7 = ("OK RAIZES PROFUNDAS" if de<=2 else "MODERADA" if de<=3 else "ELEVADA" if de<=4 else "AVA-2 RISCO DE RUINA")
                c7 += f"| {a['ticker']:<8} | {de:>8.1f}x | {d7:<29} |\n"
            c7 += "+----------+-----------+-------------------------------+\n"
            st.code(c7, language="text")

        # C.8 Indexadores
        st.markdown("### C.8 - Raio-X de Indexadores")
        pcdi = sum(a["pct"] for a in ativos_c if "PAPEL" in a["tipo"].upper())
        pipca = 100 - pcdi
        al_cdi = "ALERTA CDI>70% sensivel queda Selic" if pcdi > 70 else "OK"
        st.code(f"""\
+-------------------+-------+------------------------------------------+
| Indexador         |   %   | Alerta                                   |
+-------------------+-------+------------------------------------------+
| CDI (FII Papel)   |{pcdi:>5.1f}% | {al_cdi:<40} |
| IPCA+/Operacional |{pipca:>5.1f}% |                                          |
+-------------------+-------+------------------------------------------+""", language="text")

        # C.9 LIQUIDEZ - Patch Milhoes/Bilhoes
        st.markdown("### C.9 - Filtro de Liquidez Diaria (Patch Milhoes/Bilhoes)")
        c9 = "+----------+-----------------------------+------------------------------------+\n"
        c9 += "| Ticker   | Liquidez (interpretada)     | Diagnostico                        |\n"
        c9 += "+----------+-----------------------------+------------------------------------+\n"
        for a in ativos_c:
            lv = a.get("liquidez")
            lr = a.get("liquidez_raw","")
            ld, la2 = avaliar_liquidez(lv)
            lf = fmt_liquidez(lv)
            c9 += f"| {a['ticker']:<8} | {lf:<27} | {ld[:34]:<34} |\n"
        c9 += "+----------+-----------------------------+------------------------------------+\n"
        c9 += "NOTA: 'R$ 557,42 Milhoes' = R$ 557.420.000 (interpretacao correta Patch Liquidez)\n"
        st.code(c9, language="text")

        # Avisos AVA liquidez
        for a in ativos_c:
            _, la2 = avaliar_liquidez(a.get("liquidez"))
            if la2:
                st.markdown(f'<div class="ava-alert">AVA-2 LIQUIDEZ [{a["ticker"]}]: {fmt_liquidez(a.get("liquidez"))} &lt; R$1M/dia</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.code(RODAPE, language="text")
        if FPDF_OK:
            rel_c = AVISO_LEGAL+"\nMODULO C - VISAO DO BOSQUE\n"+fmt_ancora(MA,int(cp_ui))+"\n"+mapa+"\n"+h+f"\nScore Ponderado: {sc_pond}/100\n"+RODAPE
            st.download_button("Baixar Relatorio Consolidado PDF", gerar_pdf(rel_c),
                f"RENDA_Carteira_{date.today()}.pdf", "application/pdf", use_container_width=True)
