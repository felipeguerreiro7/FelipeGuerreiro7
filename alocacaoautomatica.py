import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import database as db
import re
import requests
from collections import defaultdict
try:
    import yfinance as yf
    _YF_OK = True
except ImportError:
    _YF_OK = False

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Alpha Alocacao", layout="wide", page_icon="📊")
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp{background-color:#0F172A;font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background-color:#1E293B;border-right:1px solid #334155;}
[data-testid="stSidebar"] *{color:#CBD5E1 !important;}
html,body,[class*="css"],p,span,div{color:#E2E8F0;}
h1{color:#F1F5F9 !important;font-size:1.6rem !important;font-weight:700 !important;}
h2,h3{color:#93C5FD !important;font-weight:600 !important;font-size:1.05rem !important;}
div[data-testid="metric-container"]{background-color:#1E293B;border:1px solid #334155;border-radius:10px;padding:18px 20px;box-shadow:0 2px 8px rgba(0,0,0,0.3);}
div[data-testid="metric-container"]:hover{border-color:#3B82F6;transition:border-color 0.2s ease;}
div[data-testid="stMetricLabel"]>div{color:#94A3B8 !important;font-size:0.82rem;font-weight:500;}
div[data-testid="stMetricValue"]{color:#F1F5F9 !important;font-size:1.5rem !important;font-weight:700;}
.stTabs [data-baseweb="tab-list"]{background-color:#1E293B;border-radius:8px;padding:4px;gap:4px;border:1px solid #334155;}
.stTabs [data-baseweb="tab"]{background-color:transparent;border-radius:6px;color:#94A3B8 !important;font-weight:500;font-size:0.88rem;padding:8px 18px;}
.stTabs [aria-selected="true"]{background-color:#3B82F6 !important;color:#FFFFFF !important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:20px;}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background-color:#1E293B !important;border:1px solid #334155 !important;border-radius:8px !important;color:#F1F5F9 !important;font-size:0.9rem;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:#3B82F6 !important;box-shadow:0 0 0 2px rgba(59,130,246,0.2) !important;}
.stTextInput label,.stNumberInput label,.stTextArea label{color:#94A3B8 !important;font-size:0.82rem;font-weight:500;}
.stButton>button{background-color:#3B82F6;color:#FFFFFF;border:none;border-radius:8px;padding:10px 22px;font-weight:600;font-size:0.88rem;transition:background-color 0.2s ease,transform 0.1s ease;}
.stButton>button:hover{background-color:#2563EB;transform:translateY(-1px);}
.stRadio label{color:#CBD5E1 !important;font-size:0.88rem;}
hr{border-color:#334155 !important;}
[data-testid="stFileUploader"]{background-color:#1E293B;border:1px dashed #334155;border-radius:10px;padding:8px;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0F172A;}
::-webkit-scrollbar-thumb{background:#334155;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#3B82F6;}
</style>''', unsafe_allow_html=True)

# ─── Inicializa banco ─────────────────────────────────────────────────────────
db.inicializar()

# ─── Perfis de alocacao ───────────────────────────────────────────────────────
# Chaves devem bater exatamente com os nomes de classe no banco SQLite
PERFIS = {
    "Ultra-conservador": {
        "Reserva de Liquidez": {"target": 30, "min": 20, "max": None},
        "RF Inflacao/Pre":     {"target": 25, "min": 20, "max": 30},
        "RF Pos-Fixada":       {"target": 35, "min": 25, "max": 40},
        "Acoes":               {"target":  4, "min":  0, "max":  9},
        "Fundos Imobiliarios": {"target":  2, "min":  0, "max":  5},
        "Alternativos":        {"target":  2, "min":  0, "max":  7},
        "Offshore":            {"target":  2, "min":  0, "max":  7},
    },
    "Conservador": {
        "Reserva de Liquidez": {"target": 20, "min": 20, "max": None},
        "RF Inflacao/Pre":     {"target": 20, "min": 15, "max": 25},
        "RF Pos-Fixada":       {"target": 35, "min": 25, "max": 40},
        "Acoes":               {"target": 15, "min": 10, "max": 20},
        "Fundos Imobiliarios": {"target":  5, "min":  0, "max":  5},
        "Alternativos":        {"target":  3, "min":  0, "max":  8},
        "Offshore":            {"target":  2, "min":  0, "max":  7},
    },
    "Moderado": {
        "Reserva de Liquidez": {"target": 15, "min": 15, "max": None},
        "RF Inflacao/Pre":     {"target": 20, "min": 15, "max": 25},
        "RF Pos-Fixada":       {"target": 25, "min": 15, "max": 30},
        "Acoes":               {"target": 25, "min": 10, "max": 30},
        "Fundos Imobiliarios": {"target":  5, "min":  0, "max": 10},
        "Alternativos":        {"target":  5, "min":  0, "max":  8},
        "Offshore":            {"target":  5, "min":  0, "max":  5},
    },
    "Arrojado": {
        "Reserva de Liquidez": {"target": 10, "min": 10, "max": None},
        "RF Inflacao/Pre":     {"target": 15, "min": 10, "max": 20},
        "RF Pos-Fixada":       {"target": 20, "min": 15, "max": 25},
        "Acoes":               {"target": 35, "min": 30, "max": 40},
        "Fundos Imobiliarios": {"target":  3, "min":  0, "max": 10},
        "Alternativos":        {"target":  7, "min":  2, "max": 12},
        "Offshore":            {"target": 10, "min":  0, "max": 15},
    },
}

# Mapeamento: nome no banco (com acento) → chave no PERFIS (sem acento)
# Necessario porque o banco armazena com acento
CLASSE_PARA_PERFIL = {
    "Reserva de Liquidez":  "Reserva de Liquidez",
    "RF Inflação/Pré":      "RF Inflacao/Pre",
    "RF Pós-Fixada":        "RF Pos-Fixada",
    "Ações":                "Acoes",
    "Fundos Imobiliários":  "Fundos Imobiliarios",
    "Alternativos":         "Alternativos",
    "Alternativo":          "Alternativos",
    "Offshore":             "Offshore",
    "Multimercado":         "Multimercado",
}
# Inverso: chave no PERFIS → nome canonico para exibicao
PERFIL_PARA_DISPLAY = {v: k for k, v in CLASSE_PARA_PERFIL.items()}

# ─── Regras internas de Acoes ─────────────────────────────────────────────────
REGRAS_ACOES = {
    "Acoes Individuais": 40,
    "BMMT11":            30,
    "QLBR11":            30,
    "FIAS":               0,
}

# ─── Lista de ativos suspensos ─────────────────────────────────────────────────
SUSPENSOS = {"GRAZZIOTIN", "GRZO3"}

# ─── Paleta de cores ──────────────────────────────────────────────────────────
_PALETA = [
    "#3B82F6","#10B981","#F59E0B","#8B5CF6","#EF4444",
    "#06B6D4","#F97316","#84CC16","#EC4899","#6B7280",
]
_CORES_FIXAS = {
    "Acoes":                "#3B82F6",
    "Ações":                "#3B82F6",
    "Fundos Imobiliarios":  "#10B981",
    "Fundos Imobiliários":  "#10B981",
    "RF Pos-Fixada":        "#F59E0B",
    "RF Pós-Fixada":        "#F59E0B",
    "RF Inflacao/Pre":      "#FBBF24",
    "RF Inflação/Pré":      "#FBBF24",
    "Reserva de Liquidez":  "#34D399",
    "Offshore":             "#8B5CF6",
    "Multimercado":         "#06B6D4",
    "Alternativos":         "#F97316",
    "Alternativo":          "#F97316",
    "Cripto":               "#EF4444",
    "Outros":               "#6B7280",
}

def cor(classe, idx=0):
    return _CORES_FIXAS.get(classe, _PALETA[idx % len(_PALETA)])


# ─── Normalizacao de nomes de classes ─────────────────────────────────────────
# Unifica variações do banco para um único nome canônico
NORM_CLASSES = {
    "Alternativo":         "Alternativos",
    "Ações":               "Ações",
    "Fundos Imobiliários": "Fundos Imobiliários",
    "RF Inflação/Pré":     "RF Inflação/Pré",
    "RF Pós-Fixada":       "RF Pós-Fixada",
}

def normalizar_classe(cls):
    return NORM_CLASSES.get(cls, cls)


# ─── Classes dinamicas ────────────────────────────────────────────────────────
def _todas_classes():
    df = db.listar_todos()
    db_cls = []
    seen = set()
    if not df.empty:
        for c in df["classe"].dropna().unique():
            c_n = normalizar_classe(c)
            if c_n not in seen:
                db_cls.append(c_n)
                seen.add(c_n)
    base = []
    seen_base = set()
    for c in PERFIL_PARA_DISPLAY.values():
        c_n = normalizar_classe(c)
        if c_n not in seen_base:
            base.append(c_n)
            seen_base.add(c_n)
    return list(dict.fromkeys(db_cls + base))


# ─── Funcoes auxiliares ───────────────────────────────────────────────────────
def formatar_valor(v):
    try:
        s = str(v).strip()
        s = re.sub(r'[^\d,\.\-]', '', s)
        if ',' in s and '.' in s:
            if s.index(',') > s.index('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def limpar_ticker(nome):
    m = re.match(r'^([A-Z]{3,5}\d{1,2}[A-Z]?)', nome.upper().strip())
    return m.group(1) if m else nome.upper().strip()[:8]


def classificar_ativo_mestre(nome):
    classe, _ = db.buscar(nome)
    if classe:
        return normalizar_classe(classe)

    t = limpar_ticker(nome).upper()
    nome_up = nome.upper()

    for p in ["TESOURO", "CDB", "LCI", "LCA", "CRI", "CRA", "DEBENTURE", "LFT", "LTN", "NTN", "RDB"]:
        if p in nome_up:
            return "RF Pós-Fixada"

    for p in ["BTC", "ETH", "BITCOIN", "ETHEREUM", "CRIPTO"]:
        if p in nome_up:
            return "Alternativos"

    if re.match(r'^[A-Z]{4}(3[2345]|3B)$', t):
        return "Offshore"

    for e in ["IVVB", "SPY", "QQQ", "HASH"]:
        if t.startswith(e):
            return "Offshore"

    if re.match(r'^[A-Z]{4}11$', t):
        return "Fundos Imobiliários"

    if re.match(r'^[A-Z]{4}[3456]$', t):
        return "Ações"

    return "Outros"


def br(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _preco_yfinance(ticker: str):
    if not _YF_OK:
        return None
    try:
        t = ticker.upper()
        if not t.endswith(".SA"):
            t += ".SA"
        info = yf.Ticker(t).fast_info
        p = info.last_price
        return float(p) if p and p > 0 else None
    except Exception:
        return None


def _preco_brapi(ticker: str):
    """Fallback via brapi.dev (gratuito, sem chave)."""
    try:
        t = ticker.upper().replace(".SA", "")
        r = requests.get(
            f"https://brapi.dev/api/quote/{t}",
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                p = results[0].get("regularMarketPrice")
                return float(p) if p and p > 0 else None
    except Exception:
        pass
    return None


def _preco_statusinvest(ticker: str):
    """Fallback via Status Invest (scraping da cotação)."""
    try:
        t = ticker.upper().replace(".SA", "")
        url = f"https://statusinvest.com.br/acoes/{t.lower()}"
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            m = re.search(r'"price"\s*:\s*([0-9]+[,.]?[0-9]*)', r.text)
            if not m:
                # tenta fundos/FIIs
                url_fii = f"https://statusinvest.com.br/fundos-imobiliarios/{t.lower()}"
                r2 = requests.get(url_fii, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
                if r2.status_code == 200:
                    m = re.search(r'"price"\s*:\s*([0-9]+[,.]?[0-9]*)', r2.text)
            if m:
                p = float(m.group(1).replace(",", "."))
                return p if p > 0 else None
    except Exception:
        pass
    return None


@st.cache_data(ttl=300, show_spinner=False)
def obter_preco(ticker: str):
    """Retorna o último preço tentando yfinance → brapi.dev → Status Invest."""
    t = ticker.upper().replace(".SA", "")
    p = _preco_yfinance(t)
    if p:
        return p
    p = _preco_brapi(t)
    if p:
        return p
    p = _preco_statusinvest(t)
    return p


def parse_excel(arquivo):
    carteira_lida = defaultdict(float)
    ativos_detalhados = []
    saldo_corretora = 0.0
    conta_id = ""

    df_raw = pd.read_excel(arquivo, header=None)

    # índices padrão para a aba de ações (ajustados ao detectar cabeçalhos)
    idx_ativo = 0
    idx_pos   = 11   # coluna "Posição" no extrato de ações
    idx_qtd   = 7    # "Qtd. Total"
    idx_pm    = 8    # "Preço Médio"

    # seções que NÃO contêm ativos a capturar
    SECOES_IGNORAR = [
        "PROVENTO", "DIVIDENDO", "JCP", "RENDIMENTO A RECEBER",
        "OPCAO", "OPÇÃO", "DERIVATIVO", "TERMO", "GARANTIA",
        "OPERACAO", "OPERAÇÃO", "POSICAO ABERTA",
    ]
    skip_section = False  # flag para ignorar seção atual

    def find_col(cols, *terms):
        """Retorna o índice da primeira coluna cujo texto bate com um dos termos."""
        for term in terms:
            for i, c in enumerate(cols):
                if str(c).strip().upper() == term.upper():
                    return i
        return None

    def find_col_contains(cols, *terms):
        """Retorna o índice da primeira coluna que CONTÉM um dos termos."""
        for term in terms:
            for i, c in enumerate(cols):
                if term.upper() in str(c).strip().upper():
                    return i
        return None

    for i, row in df_raw.iterrows():
        # texto completo da linha (maiúsculas) para detecção rápida
        txt = " ".join([str(x).upper() for x in row if str(x).strip() not in ("", "NAN")])

        # ── captura conta ──────────────────────────────────────────────────────
        for cell in row:
            s = str(cell)
            if "Conta:" in s or "CONTA:" in s:
                conta_id = s.split("|")[0].replace("Conta:", "").replace("CONTA:", "").strip()
                break

        # ── captura saldo disponível ────────────────────────────────────────────
        if "SALDO DISPONIVEL" in txt or "SALDO DISPONÍVEL" in txt:
            try:
                next_row = df_raw.iloc[i + 1]
                for col_idx in [2, 1, 0]:
                    v = formatar_valor(next_row.iloc[col_idx])
                    if v > 0:
                        saldo_corretora = v
                        break
            except Exception:
                pass

        # ── detecção de cabeçalho de tabela ────────────────────────────────────
        # Acionado quando a linha tem colunas típicas de tabela de ativos
        cols_u = [str(x).strip().upper() for x in row]
        tem_valor_liq = any("VALOR L" in c for c in cols_u)   # "Valor Líquido"
        tem_posicao   = any("POSI" in c for c in cols_u)
        tem_data_cota = any("DATA COTA" in c for c in cols_u)
        tem_ativo     = "ATIVO" in cols_u

        is_header = (
            (tem_ativo and tem_posicao)                   # extrato de ações/BDRs
            or (tem_data_cota and (tem_posicao or tem_valor_liq))  # extrato de fundos
            or tem_valor_liq                              # qualquer tabela com Valor Líquido
        )

        if is_header:
            ia = find_col(cols_u, "ATIVO")
            if ia is None:
                ia = 0  # fundos: nome ocupa a primeira coluna

            # Valor Líquido preferido sobre Posição (desconta cotas em cotização)
            ip = find_col_contains(cols_u, "VALOR L")
            if ip is None:
                ip = find_col_contains(cols_u, "POSIÇÃO", "POSICAO", "POSI\u00c7\u00c3O")
            if ip is not None:
                idx_ativo, idx_pos = ia, ip

            iq = find_col(cols_u, "QTD. TOTAL", "QTDE.", "QUANTIDADE", "QTD. COTAS", "QTDE. COTAS")
            if iq is not None:
                idx_qtd = iq

            ipm = find_col_contains(cols_u, "PREÇO M", "PRECO M")
            if ipm is not None:
                idx_pm = ipm

            continue  # não processar a linha de cabeçalho como ativo

        # ── nome do ativo na linha atual ───────────────────────────────────────
        nome_p = str(row.iloc[idx_ativo]).strip() if idx_ativo < len(row) else ""

        # ── detecção de cabeçalho de seção (ex: "10,6%|Ações") ────────────────
        if re.search(r'^\d+[,\.]?\d*\s*%', nome_p) and '|' in nome_p:
            # determina se a seção é de ativos ou deve ser ignorada
            nome_sec = nome_p.split('|', 1)[1].strip().upper()
            skip_section = any(ign in nome_sec for ign in SECOES_IGNORAR)
            continue  # próprio cabeçalho nunca é um ativo

        # ── pula linhas de seções não-investimento ─────────────────────────────
        if skip_section:
            continue

        # ── pula linhas claramente não-ativo ──────────────────────────────────
        if nome_p in ("nan", "", "None") or "TOTAL" in nome_p.upper():
            continue

        # ── lê valor da posição ────────────────────────────────────────────────
        try:
            v_pos = formatar_valor(row.iloc[idx_pos]) if idx_pos < len(row) else 0.0
        except Exception:
            v_pos = 0.0

        if v_pos < 1.0:
            continue

        cat = classificar_ativo_mestre(nome_p)
        carteira_lida[cat] += v_pos
        suspenso = limpar_ticker(nome_p) in SUSPENSOS or nome_p.upper() in SUSPENSOS

        ativos_detalhados.append({
            "Ativo":    nome_p,
            "Ticker":   limpar_ticker(nome_p),
            "Qtd":      formatar_valor(row.iloc[idx_qtd]) if idx_qtd < len(row) else 0.0,
            "PM":       formatar_valor(row.iloc[idx_pm])  if idx_pm  < len(row) else 0.0,
            "Total":    v_pos,
            "Cat":      cat,
            "Suspenso": suspenso,
        })

    return carteira_lida, ativos_detalhados, saldo_corretora, conta_id


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload")
    arquivo = st.file_uploader("Extrato Excel da corretora", type=["xlsx", "xls"])

    st.markdown("---")
    st.header("Perfil de Alocacao")

    opcoes_perfil = ["Manual"] + list(PERFIS.keys())
    perfil_sel = st.selectbox("Perfil", opcoes_perfil, key="perfil_sel")

    st.markdown("---")
    st.header("Alocacao Alvo (%)")

    CLASSES = _todas_classes()
    alvo = {}
    total_alvo = 0

    for cls in CLASSES:
        # Busca o target do perfil pela chave sem acento
        chave_perfil = CLASSE_PARA_PERFIL.get(cls, cls)
        info_perfil = PERFIS.get(perfil_sel, {}).get(chave_perfil, {}) if perfil_sel != "Manual" else {}
        target_val = info_perfil.get("target", 0)
        min_val = info_perfil.get("min")
        max_val = info_perfil.get("max")

        hint = ""
        if info_perfil:
            min_s = f"{min_val}%" if min_val is not None else "-"
            max_s = f"{max_val}%" if max_val is not None else "-"
            hint = f"  _(min {min_s} | max {max_s})_"

        label = f"{cls}{hint}"
        val = st.number_input(
            label, min_value=0, max_value=100,
            value=target_val, step=5,
            key=f"alvo_{cls}_{perfil_sel}",
        )
        alvo[cls] = val
        total_alvo += val

    if total_alvo != 100:
        st.warning(f"Total: {total_alvo}% (precisa ser 100%)")
    else:
        st.success(f"Total: 100% OK")

    st.markdown("---")
    st.header("Aporte")
    aporte = st.number_input("Valor para aportar (R$)", min_value=0.0, step=100.0, value=0.0)


# ─── Titulo ───────────────────────────────────────────────────────────────────
st.title("Alpha Alocacao")
if perfil_sel != "Manual":
    st.caption(f"Perfil: **{perfil_sel}**")

if not arquivo:
    st.info("Faca upload do extrato Excel da corretora para comecar a analise.")

    # Mostra perfis disponíveis
    st.markdown("---")
    st.subheader("Perfis de Alocacao Disponiveis")
    col_perfis = st.columns(len(PERFIS))
    for idx, (nome_p, dados_p) in enumerate(PERFIS.items()):
        with col_perfis[idx]:
            st.markdown(f"**{nome_p}**")
            for cls_k, v in dados_p.items():
                display = PERFIL_PARA_DISPLAY.get(cls_k, cls_k)
                min_s = f"{v['min']}%" if v['min'] is not None else "-"
                max_s = f"{v['max']}%" if v['max'] is not None else "-"
                st.markdown(f"- {display}: **{v['target']}%** _(min {min_s} | max {max_s})_")

    st.markdown("---")
    st.subheader("Regras de Acoes")
    col_ra1, col_ra2 = st.columns([1, 2])
    with col_ra1:
        rows_ra = [{"Componente": k, "% dentro de Acoes": f"{v}%"} for k, v in REGRAS_ACOES.items()]
        st.dataframe(pd.DataFrame(rows_ra), use_container_width=True, hide_index=True)
    with col_ra2:
        st.info(
            "Dentro da alocacao em **Acoes**, a distribuicao segue:\n\n"
            "- **40%** → acoes individuais (dividido igualmente entre ativos Padrao)\n"
            "- **30%** → BMMT11\n"
            "- **30%** → QLBR11\n"
            "- Ativos **Suspensos** (ex: Grazziotin) nao recebem aporte"
        )

    st.markdown("---")
    st.subheader("Base de Classificacoes")
    n = db.contar()
    st.write(f"Total de ativos classificados no banco: **{n}**")
    if n > 0:
        st.dataframe(db.listar_todos(), use_container_width=True, hide_index=True)
    st.stop()

# ─── Processa extrato ─────────────────────────────────────────────────────────
with st.spinner("Processando extrato..."):
    carteira_lida, ativos_detalhados, saldo_corretora, conta_id = parse_excel(arquivo)

for cls in CLASSES:
    carteira_lida.setdefault(cls, 0.0)
for cls in list(carteira_lida.keys()):
    if cls not in CLASSES:
        CLASSES.append(cls)
        alvo[cls] = 0

patrimonio_total = sum(carteira_lida.values()) + saldo_corretora

if patrimonio_total == 0:
    st.error("Nao foi possivel ler valores do extrato. Verifique o formato do arquivo.")
    st.stop()

# ─── Metricas ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Patrimonio Total", br(patrimonio_total))
c2.metric("Saldo Disponivel", br(saldo_corretora))
c3.metric("Ativos na Carteira", len(ativos_detalhados))
c4.metric("Conta", conta_id if conta_id else "-")

st.markdown("---")

# ─── Abas ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Carteira Atual", "Ativos", "Sugestao de Alocacao",
    "Ordens e E-mails", "Regras de Acoes", "Classificacoes"
])

# ══════════════════════════════════════════════════════
# TAB 1 – CARTEIRA ATUAL
# ══════════════════════════════════════════════════════
with tab1:
    labels = [c for c in CLASSES if carteira_lida.get(c, 0) > 0]
    values = [carteira_lida[c] for c in labels]
    cores_lista = [cor(c, i) for i, c in enumerate(labels)]

    col_pizza, col_barras = st.columns(2)

    with col_pizza:
        st.subheader("Distribuicao Atual")
        fig_pizza = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=cores_lista, hole=0.45,
            textinfo="label+percent", textfont_size=12,
        ))
        fig_pizza.update_layout(
            paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
            font_color="#E2E8F0", showlegend=True,
            legend=dict(font=dict(color="#CBD5E1")),
            margin=dict(t=20, b=20, l=20, r=20), height=400,
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_barras:
        st.subheader("Atual vs Alvo")
        atual_pct = {c: carteira_lida.get(c, 0) / patrimonio_total * 100 for c in CLASSES}

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Atual", x=CLASSES,
            y=[atual_pct[c] for c in CLASSES],
            marker_color=[cor(c, i) for i, c in enumerate(CLASSES)], opacity=0.9,
        ))
        fig_bar.add_trace(go.Bar(
            name="Alvo", x=CLASSES,
            y=[alvo.get(c, 0) for c in CLASSES],
            marker_color="#475569", opacity=0.6,
        ))

        # faixas min/max do perfil como shapes
        shapes = []
        if perfil_sel != "Manual":
            for xi, cls in enumerate(CLASSES):
                chave = CLASSE_PARA_PERFIL.get(cls, cls)
                info = PERFIS[perfil_sel].get(chave, {})
                mn = info.get("min")
                mx = info.get("max")
                if mn is not None:
                    shapes.append(dict(
                        type="line", xref="x", yref="y",
                        x0=xi - 0.4, x1=xi + 0.4, y0=mn, y1=mn,
                        line=dict(color="#34D399", width=2, dash="dot"),
                    ))
                if mx is not None:
                    shapes.append(dict(
                        type="line", xref="x", yref="y",
                        x0=xi - 0.4, x1=xi + 0.4, y0=mx, y1=mx,
                        line=dict(color="#EF4444", width=2, dash="dot"),
                    ))

        fig_bar.update_layout(
            barmode="group", shapes=shapes,
            paper_bgcolor="#0F172A", plot_bgcolor="#1E293B",
            font_color="#E2E8F0",
            legend=dict(font=dict(color="#CBD5E1")),
            yaxis=dict(title="(%)", gridcolor="#334155"),
            xaxis=dict(gridcolor="#334155", tickangle=-30),
            margin=dict(t=20, b=80, l=20, r=20), height=420,
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        if perfil_sel != "Manual":
            st.caption("— — verde: mínimo do perfil | — — vermelho: máximo do perfil")

    st.subheader("Resumo por Classe")
    rows_resumo = []
    for c in CLASSES:
        val = carteira_lida.get(c, 0)
        pct_atual = val / patrimonio_total * 100
        pct_alvo = alvo.get(c, 0)
        diff = pct_atual - pct_alvo

        chave = CLASSE_PARA_PERFIL.get(c, c)
        info = PERFIS.get(perfil_sel, {}).get(chave, {}) if perfil_sel != "Manual" else {}
        mn = info.get("min")
        mx = info.get("max")

        status = ""
        if info:
            if mn is not None and pct_atual < mn:
                status = "Abaixo do min"
            elif mx is not None and pct_atual > mx:
                status = "Acima do max"
            else:
                status = "Ok"

        rows_resumo.append({
            "Classe":            c,
            "Valor":             br(val),
            "Atual (%)":         f"{pct_atual:.1f}%",
            "Alvo (%)":          f"{pct_alvo:.0f}%",
            "Diferenca (p.p.)":  f"{diff:+.1f}",
            "Status":            status,
        })
    st.dataframe(pd.DataFrame(rows_resumo), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
# TAB 2 – ATIVOS DETALHADOS
# ══════════════════════════════════════════════════════
with tab2:
    st.subheader("Posicoes Detalhadas")
    if ativos_detalhados:
        df_ativos = pd.DataFrame(ativos_detalhados)
        classes_presentes = sorted(df_ativos["Cat"].unique())
        filtro = st.multiselect("Filtrar por classe", classes_presentes, default=classes_presentes)
        df_f = df_ativos[df_ativos["Cat"].isin(filtro)].copy()
        df_f["% Cart."] = (df_f["Total"] / patrimonio_total * 100).map("{:.2f}%".format)
        df_f["Total (R$)"] = df_f["Total"].map(br)
        df_f["PM (R$)"] = df_f["PM"].map(lambda x: br(x) if x > 0 else "-")
        df_f["Qtd"] = df_f["Qtd"].map(lambda x: f"{x:,.0f}" if x > 0 else "-")
        df_f["Situacao"] = df_f["Suspenso"].map(lambda x: "Suspenso" if x else "Padrao")

        st.dataframe(
            df_f[["Ativo", "Ticker", "Cat", "Situacao", "Qtd", "PM (R$)", "Total (R$)", "% Cart."]],
            use_container_width=True, hide_index=True,
        )

        st.markdown("---")
        st.subheader("Corrigir Classificacao")
        ca, cb, cc = st.columns([2, 1, 1])
        with ca:
            ativo_sel = st.selectbox("Ativo", [a["Ativo"] for a in ativos_detalhados])
        with cb:
            nova_classe = st.selectbox("Nova Classe", CLASSES)
        with cc:
            nova_sub = st.text_input("Subclasse (opcional)")
        if st.button("Salvar"):
            db.salvar(ativo_sel, nova_classe, nova_sub)
            st.success(f"'{ativo_sel}' salvo como '{nova_classe}'. Recarregue para aplicar.")
    else:
        st.info("Nenhum ativo encontrado no extrato.")


# ══════════════════════════════════════════════════════
# TAB 3 – SUGESTAO DE ALOCACAO
# ══════════════════════════════════════════════════════
with tab3:
    st.subheader("Sugestao de Alocacao")

    if total_alvo != 100:
        st.warning("Ajuste os percentuais alvo na barra lateral para totalizar 100%.")
    else:
        capital_total = patrimonio_total + aporte

        rows_sug = []
        for c in CLASSES:
            valor_atual = carteira_lida.get(c, 0)
            valor_alvo = capital_total * alvo.get(c, 0) / 100
            diff_val = valor_alvo - valor_atual
            pct_atual = valor_atual / patrimonio_total * 100

            if diff_val > 50:
                acao = f"Comprar {br(diff_val)}"
            elif diff_val < -50:
                acao = f"Vender {br(abs(diff_val))}"
            else:
                acao = "OK"

            rows_sug.append({
                "Classe": c,
                "Atual (R$)": br(valor_atual),
                "Atual (%)": f"{pct_atual:.1f}%",
                "Alvo (%)": f"{alvo.get(c, 0):.0f}%",
                "Alvo (R$)": br(valor_alvo),
                "Acao": acao,
            })

        st.dataframe(pd.DataFrame(rows_sug), use_container_width=True, hide_index=True)

        # gráfico delta
        st.subheader("Delta por Classe (R$)")
        deltas = [capital_total * alvo.get(c, 0) / 100 - carteira_lida.get(c, 0) for c in CLASSES]
        cores_delta = ["#10B981" if d >= 0 else "#EF4444" for d in deltas]
        fig_wf = go.Figure(go.Bar(
            x=CLASSES, y=deltas, marker_color=cores_delta,
            text=[f"R$ {d:+,.0f}".replace(",", ".") for d in deltas],
            textposition="outside",
        ))
        fig_wf.update_layout(
            paper_bgcolor="#0F172A", plot_bgcolor="#1E293B", font_color="#E2E8F0",
            yaxis=dict(title="Delta R$", gridcolor="#334155", zeroline=True, zerolinecolor="#475569"),
            xaxis=dict(gridcolor="#334155", tickangle=-30),
            margin=dict(t=40, b=80, l=20, r=20), height=380,
        )
        st.plotly_chart(fig_wf, use_container_width=True)

        # ── Detalhamento dentro de Acoes ──────────────────────────────────────
        cls_acoes = next((c for c in CLASSES if "ao" in c.lower() or "ção" in c.lower()), None)
        total_acoes_alvo = capital_total * alvo.get(cls_acoes, 0) / 100 if cls_acoes else 0

        if total_acoes_alvo > 0:
            st.markdown("---")
            st.subheader("Detalhamento: Acoes")

            # ativos de acoes nao suspensos (excluindo ETFs BMMT11 e QLBR11)
            df_acoes_raw = [a for a in ativos_detalhados
                            if a["Cat"] in (cls_acoes, "Ações")
                            and not a["Suspenso"]
                            and a["Ticker"] not in ("BMMT11", "QLBR11")]
            n_acoes_ind = len(df_acoes_raw)

            rows_det = []
            for comp, pct_comp in REGRAS_ACOES.items():
                valor_comp_alvo = total_acoes_alvo * pct_comp / 100
                if comp == "Acoes Individuais":
                    # divide igualmente entre as acoes individuais padrao
                    if n_acoes_ind > 0:
                        por_acao = valor_comp_alvo / n_acoes_ind
                        for a in df_acoes_raw:
                            atual_ind = a["Total"]
                            diff_ind = por_acao - atual_ind
                            rows_det.append({
                                "Ativo":        a["Ativo"],
                                "Componente":   "Acao Individual",
                                "Alvo (R$)":    br(por_acao),
                                "Atual (R$)":   br(atual_ind),
                                "Acao":         f"Comprar {br(diff_ind)}" if diff_ind > 50 else
                                                f"Vender {br(abs(diff_ind))}" if diff_ind < -50 else "OK",
                            })
                    else:
                        rows_det.append({
                            "Ativo": "Nenhuma acao individual ativa", "Componente": comp,
                            "Alvo (R$)": br(valor_comp_alvo), "Atual (R$)": "-", "Acao": "-"
                        })
                else:
                    ativo_etf = next((a for a in ativos_detalhados if a["Ticker"] == comp), None)
                    atual_etf = ativo_etf["Total"] if ativo_etf else 0.0
                    diff_etf = valor_comp_alvo - atual_etf
                    rows_det.append({
                        "Ativo":      comp,
                        "Componente": "ETF",
                        "Alvo (R$)":  br(valor_comp_alvo),
                        "Atual (R$)": br(atual_etf),
                        "Acao":       f"Comprar {br(diff_etf)}" if diff_etf > 50 else
                                      f"Vender {br(abs(diff_etf))}" if diff_etf < -50 else "OK",
                    })

            st.dataframe(pd.DataFrame(rows_det), use_container_width=True, hide_index=True)

        # ── Distribuicao do aporte ────────────────────────────────────────────
        if aporte > 0:
            st.markdown("---")
            st.subheader("Como distribuir o Aporte")
            rows_ap = []
            for c in CLASSES:
                if alvo.get(c, 0) > 0:
                    diff = capital_total * alvo[c] / 100 - carteira_lida.get(c, 0)
                    aportar = max(0.0, diff)
                    if aportar > 0:
                        rows_ap.append({"Classe": c, "Aportar": br(aportar)})
            if rows_ap:
                st.dataframe(pd.DataFrame(rows_ap), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
# TAB 4 – ORDENS E E-MAILS
# ══════════════════════════════════════════════════════
with tab4:
    st.subheader("Gerador de Ordens e E-mails")

    secao_ordem, secao_email = st.tabs(["Ordens de Acoes / BDRs", "E-mail IPCA+"])

    # ── Gerador de Ordens ─────────────────────────────────────────────────────
    with secao_ordem:
        st.markdown("Calcula as quantidades a comprar com base na sugestao de alocacao e nos precos de mercado.")

        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1:
            conta_ordem = st.text_input("Numero da conta", value=conta_id if conta_id else "")
        with col_o2:
            formato_ordem = st.selectbox("Formato", ["XP (planilha)", "BTG (e-mail)"])
        with col_o3:
            buscar_precos = st.button("Buscar precos e gerar ordens")

        if total_alvo != 100:
            st.warning("Configure os alvos na sidebar (total = 100%) para gerar ordens.")
        elif buscar_precos:
            capital_total_ord = patrimonio_total + aporte

            # Descobre a chave de classe de ações (nome com acento ou sem)
            cls_ac = next((c for c in CLASSES if "o" in c.lower() and len(c) <= 6), None)

            total_acoes_alvo_ord = capital_total_ord * alvo.get(cls_ac, 0) / 100 if cls_ac else 0
            total_offshore_alvo  = capital_total_ord * alvo.get("Offshore", 0) / 100
            total_alt_alvo       = capital_total_ord * alvo.get("Alternativos", 0) / 100

            # ativos individuais de ações (não ETFs, não suspensos)
            ETFS_ACOES = {"BMMT11", "QLBR11", "FIAS"}
            acoes_ind = [a for a in ativos_detalhados
                         if normalizar_classe(a["Cat"]) == cls_ac
                         and a["Ticker"] not in ETFS_ACOES
                         and not a["Suspenso"]]
            n_ind = len(acoes_ind)

            ordens = []
            erros_preco = []

            with st.spinner("Buscando precos no mercado..."):

                # ── Acoes individuais ──────────────────────────────────────────
                if n_ind > 0 and total_acoes_alvo_ord > 0:
                    alvo_por_acao = total_acoes_alvo_ord * REGRAS_ACOES.get("Acoes Individuais", 40) / 100 / n_ind
                    for a in acoes_ind:
                        delta = alvo_por_acao - a["Total"]
                        if delta < 50:
                            continue
                        preco = obter_preco(a["Ticker"])
                        if preco:
                            qty = int(delta // preco)
                            if qty > 0:
                                ordens.append({"Ativo": a["Ticker"], "C/V": "C",
                                               "Quantidade": qty, "Preco": "M",
                                               "Conta": conta_ordem, "Validade": "hoje"})
                        else:
                            erros_preco.append(a["Ticker"])

                # ── ETFs de Acoes (BMMT11, QLBR11) ────────────────────────────
                for etf, pct_etf in [("BMMT11", REGRAS_ACOES.get("BMMT11", 30)),
                                      ("QLBR11", REGRAS_ACOES.get("QLBR11", 30))]:
                    if pct_etf == 0 or total_acoes_alvo_ord == 0:
                        continue
                    alvo_etf = total_acoes_alvo_ord * pct_etf / 100
                    atual_etf = next((a["Total"] for a in ativos_detalhados if a["Ticker"] == etf), 0.0)
                    delta_etf = alvo_etf - atual_etf
                    if delta_etf < 50:
                        continue
                    preco = obter_preco(etf)
                    if preco:
                        qty = int(delta_etf // preco)
                        if qty > 0:
                            ordens.append({"Ativo": etf, "C/V": "C",
                                           "Quantidade": qty, "Preco": "M",
                                           "Conta": conta_ordem, "Validade": "hoje"})
                    else:
                        erros_preco.append(etf)

                # ── Offshore (BDRs) — distribui igualmente ─────────────────────
                bdrs = [a for a in ativos_detalhados if normalizar_classe(a["Cat"]) == "Offshore"]
                if bdrs and total_offshore_alvo > 0:
                    atual_off = sum(a["Total"] for a in bdrs)
                    delta_off = total_offshore_alvo - atual_off
                    if delta_off > 50:
                        por_bdr = delta_off / len(bdrs)
                        for a in bdrs:
                            preco = obter_preco(a["Ticker"])
                            if preco:
                                qty = int(por_bdr // preco)
                                if qty > 0:
                                    ordens.append({"Ativo": a["Ticker"], "C/V": "C",
                                                   "Quantidade": qty, "Preco": "M",
                                                   "Conta": conta_ordem, "Validade": "hoje"})
                            else:
                                erros_preco.append(a["Ticker"])

                # ── Alternativos (ex: BITH11) ──────────────────────────────────
                alts = [a for a in ativos_detalhados if normalizar_classe(a["Cat"]) == "Alternativos"
                        and re.match(r'^[A-Z]{4}11$', a["Ticker"])]
                if alts and total_alt_alvo > 0:
                    atual_alt = sum(a["Total"] for a in alts)
                    delta_alt = total_alt_alvo - atual_alt
                    if delta_alt > 50:
                        por_alt = delta_alt / len(alts)
                        for a in alts:
                            preco = obter_preco(a["Ticker"])
                            if preco:
                                qty = int(por_alt // preco)
                                if qty > 0:
                                    ordens.append({"Ativo": a["Ticker"], "C/V": "C",
                                                   "Quantidade": qty, "Preco": "M",
                                                   "Conta": conta_ordem, "Validade": "hoje"})
                            else:
                                erros_preco.append(a["Ticker"])

            if erros_preco:
                st.warning(f"Nao foi possivel obter preco de: {', '.join(erros_preco)}")

            if ordens:
                df_ord = pd.DataFrame(ordens)
                st.dataframe(df_ord, use_container_width=True, hide_index=True)

                if formato_ordem == "XP (planilha)":
                    # Texto para copiar — separado por tab (colar direto no XP)
                    linhas = ["Ativo\tC/V\tQuantidade\tPreco\tConta\tValidade"]
                    for o in ordens:
                        linhas.append(f"{o['Ativo']}\t{o['C/V']}\t{o['Quantidade']}\t{o['Preco']}\t{o['Conta']}\t{o['Validade']}")
                    st.text_area("Copiar para XP (Ctrl+A → Ctrl+C)", "\n".join(linhas), height=220)

                else:  # BTG e-mail
                    linhas_tab = ["| Ativo | Preco | C/V | Qtd. Total | Cliente |",
                                  "|-------|-------|-----|------------|---------|"]
                    for o in ordens:
                        linhas_tab.append(f"| {o['Ativo']} | M | C | {o['Quantidade']} | {o['Conta']} |")

                    corpo = (
                        f"Olá, tudo bem?\n\n"
                        f"Gostaria de formalizar a operação de ações na conta ({conta_ordem}).\n"
                        f"Conforme 'Aceito' do cliente.\n\n"
                        f"Segue abaixo:\n\n"
                        f"Ações, ETF e BDR\n\n"
                        + "\n".join(
                            f"{o['Ativo']}  |  M  |  C  |  {o['Quantidade']}  |  {o['Conta']}"
                            for o in ordens
                        )
                    )
                    st.text_area("Corpo do e-mail BTG (copiar)", corpo, height=280)
            else:
                st.info("Nenhuma ordem gerada. Verifique se ha saldo/aporte suficiente e se os alvos estao configurados.")

    # ── Gerador de E-mail IPCA+ ───────────────────────────────────────────────
    with secao_email:
        st.markdown("Gera o e-mail padrao de solicitacao de aceite para compra de Tesouro IPCA+.")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            nome_cliente = st.text_input("Nome do cliente")
            conta_email  = st.text_input("Numero da conta", value=conta_id if conta_id else "", key="conta_email_ipca")
        with col_e2:
            valor_ipca = st.number_input("Valor (R$)", min_value=0.0, step=500.0, value=0.0)
            titulo_ipca = st.selectbox("Titulo IPCA+",
                ["IPCA+ 2026", "IPCA+ 2029", "IPCA+ 2032", "IPCA+ 2035",
                 "IPCA+ 2040", "IPCA+ 2045", "IPCA+ 2050", "IPCA+ 2055"])

        if st.button("Gerar E-mail IPCA+"):
            if not nome_cliente or valor_ipca <= 0:
                st.warning("Preencha o nome do cliente e o valor.")
            else:
                valor_fmt = f"R$ {valor_ipca:,.0f}".replace(",", ".")
                email_ipca = (
                    f"Olá, {nome_cliente}, bom dia! Tudo bem?\n\n"
                    f"Gostaria de solicitar, por gentileza, o aceite para execução das seguintes compras em Tesouro IPCA+:\n\n"
                    f"{valor_fmt} em {titulo_ipca}\n\n"
                    f"Será realizado com o saldo em conta, a conta é a de número ({conta_email}).\n\n"
                    f'Basta responder esse E-mail com "Aceito".'
                )
                st.text_area("E-mail gerado (copiar)", email_ipca, height=220)


# ══════════════════════════════════════════════════════
# TAB 5 – REGRAS DE ACOES
# ══════════════════════════════════════════════════════
with tab5:
    st.subheader("Regras de Composicao: Acoes")

    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        st.markdown("**Distribuicao interna**")
        rows_ra = [{"Componente": k, "% dentro de Acoes": f"{v}%"} for k, v in REGRAS_ACOES.items()]
        st.dataframe(pd.DataFrame(rows_ra), use_container_width=True, hide_index=True)

        fig_ra = go.Figure(go.Pie(
            labels=[k for k, v in REGRAS_ACOES.items() if v > 0],
            values=[v for v in REGRAS_ACOES.values() if v > 0],
            hole=0.4, textinfo="label+percent",
            marker_colors=["#3B82F6", "#10B981", "#F59E0B"],
        ))
        fig_ra.update_layout(
            paper_bgcolor="#0F172A", font_color="#E2E8F0",
            margin=dict(t=20, b=20, l=10, r=10), height=260,
            showlegend=False,
        )
        st.plotly_chart(fig_ra, use_container_width=True)

    with col_r2:
        st.markdown("**Lista de ativos de Acoes**")

        df_todos = db.listar_todos()
        if not df_todos.empty:
            df_acoes_db = df_todos[df_todos["classe"].isin(["Ações", "Acoes"])].copy()
            if not df_acoes_db.empty:
                df_acoes_db["Situacao"] = df_acoes_db["nome"].apply(
                    lambda n: "Suspenso" if limpar_ticker(n) in SUSPENSOS or n.upper() in SUSPENSOS else "Padrao"
                )
                df_acoes_db["Tipo"] = df_acoes_db["nome"].apply(
                    lambda n: "ETF" if limpar_ticker(n) in ("BMMT11", "QLBR11", "FIAS") else "Acao"
                )
                st.dataframe(
                    df_acoes_db[["nome", "subclasse", "Tipo", "Situacao"]],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("Nenhuma acao cadastrada no banco. Classifique ativos na aba 'Ativos'.")
        else:
            st.info("Banco de classificacoes vazio.")

        st.markdown("**Perfis — alocacao em Acoes**")
        rows_perfil_ac = []
        for pn, pd_data in PERFIS.items():
            ac = pd_data.get("Acoes", {})
            rows_perfil_ac.append({
                "Perfil":  pn,
                "Alvo":    f"{ac.get('target', 0)}%",
                "Minimo":  f"{ac.get('min', 0)}%",
                "Maximo":  f"{ac.get('max', '-')}%" if ac.get('max') else "-",
            })
        st.dataframe(pd.DataFrame(rows_perfil_ac), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════
# TAB 6 – CLASSIFICACOES
# ══════════════════════════════════════════════════════
with tab6:
    st.subheader("Base de Classificacoes")

    col_imp, col_info = st.columns([1, 2])
    with col_imp:
        excel_db = st.file_uploader("Importar Excel de classificacoes",
                                    type=["xlsx", "xls"], key="import_db")
        if excel_db:
            try:
                n_imp = db.importar_excel(excel_db)
                st.success(f"{n_imp} novos registros importados.")
            except Exception as e:
                st.error(f"Erro: {e}")
    with col_info:
        st.info("Excel deve ter 4 colunas: nome | classe | subclasse | fonte")

    st.markdown("---")
    df_all = db.listar_todos()
    st.write(f"Total: **{len(df_all)}** registros")
    if not df_all.empty:
        busca = st.text_input("Buscar por nome")
        if busca:
            df_all = df_all[df_all["nome"].str.contains(busca, case=False, na=False)]
        st.dataframe(df_all, use_container_width=True, hide_index=True)
    else:
        st.info("Banco vazio. Use a aba 'Ativos' para classificar ou importe um Excel.")
