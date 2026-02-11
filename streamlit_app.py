import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SRO Risk Analyzer - Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #0E1117; }

    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid #2a2a4a;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-value {
        font-size: 42px;
        font-weight: 800;
        margin: 8px 0;
        line-height: 1;
    }
    .metric-label {
        font-size: 13px;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .metric-sub {
        font-size: 12px;
        color: #5a6785;
        margin-top: 4px;
    }

    /* Cards de urgência */
    .urgency-critical {
        background: linear-gradient(135deg, #2d0a0a 0%, #4a1111 100%);
        border: 1px solid #ff4b4b;
        border-radius: 12px;
        padding: 16px;
        margin: 6px 0;
    }
    .urgency-high {
        background: linear-gradient(135deg, #2d1a0a 0%, #4a2a11 100%);
        border: 1px solid #ff8c00;
        border-radius: 12px;
        padding: 16px;
        margin: 6px 0;
    }
    .urgency-medium {
        background: linear-gradient(135deg, #2d2a0a 0%, #4a4211 100%);
        border: 1px solid #ffd700;
        border-radius: 12px;
        padding: 16px;
        margin: 6px 0;
    }
    .urgency-low {
        background: linear-gradient(135deg, #0a2d0e 0%, #114a18 100%);
        border: 1px solid #00c851;
        border-radius: 12px;
        padding: 16px;
        margin: 6px 0;
    }

    /* Header da urgência */
    .urgency-header {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .urgency-count {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
    }

    /* Tabela estilizada */
    .dataframe { font-size: 13px !important; }

    /* Barra de prioridade */
    .priority-bar {
        height: 8px;
        border-radius: 4px;
        margin-top: 8px;
    }

    /* Esconder menu hamburger e footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar */
    .css-1d391kg { background-color: #0a0a1a; }

    /* Título principal */
    .main-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #ff8c00, #ffd700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 14px;
        color: #5a6785;
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════

def normalize_classification(val):
    """Normaliza as classificações para A, B, C, D"""
    if pd.isna(val) or str(val).strip() == "":
        return "Sem Classificação"
    val = str(val).strip().upper()
    if "D" in val:
        return "D"
    elif "C" in val:
        return "C"
    elif "B" in val:
        return "B"
    elif "A" in val:
        return "A"
    return "Sem Classificação"


def classify_urgency(row):
    """
    Classifica urgência com base nas regras de negócio:
    - CRÍTICO: D + >=70  OU  D + >=66
    - ALTO: C + >=66  OU  D + qualquer  OU  >=70 qualquer letra
    - MÉDIO: C + >=45  OU  B + >=66
    - BAIXO: Resto
    """
    prob = row["ProbabilityComplaintInPercent"]
    letter = row["Letra"]

    if prob < 0:
        return "⚪ SEM DADOS"

    # CRÍTICO
    if letter == "D" and prob >= 66:
        return "🔴 CRÍTICO"
    if letter == "D" and prob >= 50:
        return "🔴 CRÍTICO"

    # ALTO
    if letter == "C" and prob >= 66:
        return "🟠 ALTO"
    if letter == "D":
        return "🟠 ALTO"
    if prob >= 70:
        return "🟠 ALTO"

    # MÉDIO
    if letter == "C" and prob >= 45:
        return "🟡 MÉDIO"
    if letter == "B" and prob >= 66:
        return "🟡 MÉDIO"
    if prob >= 50:
        return "🟡 MÉDIO"

    # BAIXO
    return "🟢 BAIXO"


def urgency_sort_key(val):
    order = {"🔴 CRÍTICO": 0, "🟠 ALTO": 1, "🟡 MÉDIO": 2, "🟢 BAIXO": 3, "⚪ SEM DADOS": 4}
    return order.get(val, 5)


def get_action_recommendation(urgency, letter, prob):
    """Retorna recomendação de ação baseada na urgência"""
    actions = {
        "🔴 CRÍTICO": "🚨 INTERVENÇÃO IMEDIATA — Contatar cliente em até 2h. Escalar para supervisor. Preparar resposta para canais públicos.",
        "🟠 ALTO": "⚠️ AÇÃO EM 24H — Contato proativo obrigatório. Monitorar canais externos. Alinhar com equipe de qualidade.",
        "🟡 MÉDIO": "📋 MONITORAMENTO ATIVO — Acompanhar evolução do caso. Contato preventivo recomendado em 48h.",
        "🟢 BAIXO": "✅ MONITORAMENTO PADRÃO — Acompanhamento regular do fluxo operacional.",
        "⚪ SEM DADOS": "❓ VERIFICAR — Dados incompletos. Reprocessar análise."
    }
    return actions.get(urgency, "—")


@st.cache_data(show_spinner=False)
def load_and_process(uploaded_file):
    """Carrega e processa o Excel"""
    df = pd.read_excel(uploaded_file, sheet_name="Consulta1", engine="openpyxl")

    # Normalizar classificação
    df["Letra"] = df["Classification"].apply(normalize_classification)

    # Garantir tipos corretos
    df["ProbabilityComplaintInPercent"] = pd.to_numeric(df["ProbabilityComplaintInPercent"], errors="coerce").fillna(-1).astype(int)

    # Classificar urgência
    df["Urgência"] = df.apply(classify_urgency, axis=1)

    # Ordenar por urgência e probabilidade
    df["_sort"] = df["Urgência"].apply(urgency_sort_key)
    df = df.sort_values(["_sort", "ProbabilityComplaintInPercent"], ascending=[True, False]).drop(columns=["_sort"])

    # Recomendação
    df["Ação Recomendada"] = df.apply(lambda r: get_action_recommendation(r["Urgência"], r["Letra"], r["ProbabilityComplaintInPercent"]), axis=1)

    # Data formatada
    if "CreationDate" in df.columns:
        df["CreationDate"] = pd.to_datetime(df["CreationDate"], errors="coerce")
        df["Data"] = df["CreationDate"].dt.strftime("%d/%m/%Y %H:%M")

    return df


# ══════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ══════════════════════════════════════════════════════════════

# Header
st.markdown('<p class="main-title">🚨 SRO Risk Analyzer — Painel de Urgência</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sistema de priorização de pedidos com risco de reclamação interna (SRO) e externalização (ReclameAqui / Procon)</p>', unsafe_allow_html=True)
st.markdown("---")

# Upload
uploaded_file = st.file_uploader(
    "📎 Anexe o arquivo Excel com os dados de previsão (aba Consulta1)",
    type=["xlsx", "xls"],
    help="O arquivo deve conter a aba 'Consulta1' com as colunas: OrderId, ProbabilityComplaintInPercent, Classification, etc."
)

if uploaded_file is None:
    st.info("👆 Faça upload do arquivo Excel para iniciar a análise.")
    st.stop()

# Carregar dados
with st.spinner("⏳ Processando dados... Isso pode levar alguns segundos para arquivos grandes."):
    df = load_and_process(uploaded_file)

total = len(df)
valid = len(df[df["ProbabilityComplaintInPercent"] >= 0])

# ══════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔧 Filtros")

    # Filtro de urgência
    urgency_options = ["🔴 CRÍTICO", "🟠 ALTO", "🟡 MÉDIO", "🟢 BAIXO", "⚪ SEM DADOS"]
    selected_urgency = st.multiselect("Nível de Urgência", urgency_options, default=["🔴 CRÍTICO", "🟠 ALTO", "🟡 MÉDIO"])

    # Filtro de letra
    letter_options = sorted(df["Letra"].unique())
    selected_letters = st.multiselect("Classificação (Letra)", letter_options, default=letter_options)

    # Range de probabilidade
    prob_min, prob_max = st.slider("Faixa de Probabilidade (%)", -1, 100, (0, 100))

    # Filtro de data
    if "CreationDate" in df.columns and df["CreationDate"].notna().any():
        min_date = df["CreationDate"].min().date()
        max_date = df["CreationDate"].max().date()
        date_range = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

    # Busca por OrderId
    search_order = st.text_input("🔍 Buscar OrderId", placeholder="Ex: 2963358")

    st.markdown("---")
    st.markdown("**📊 Resumo do Arquivo**")
    st.markdown(f"- Total de registros: **{total:,}**")
    st.markdown(f"- Com dados válidos: **{valid:,}**")
    st.markdown(f"- Sem classificação: **{total - valid:,}**")

# Aplicar filtros
mask = (
    (df["Urgência"].isin(selected_urgency)) &
    (df["Letra"].isin(selected_letters)) &
    (df["ProbabilityComplaintInPercent"] >= prob_min) &
    (df["ProbabilityComplaintInPercent"] <= prob_max)
)

if date_range and len(date_range) == 2 and "CreationDate" in df.columns:
    mask = mask & (
        (df["CreationDate"].dt.date >= date_range[0]) &
        (df["CreationDate"].dt.date <= date_range[1])
    )

if search_order.strip():
    mask = mask & (df["OrderId"].astype(str).str.contains(search_order.strip()))

df_filtered = df[mask].copy()

# ══════════════════════════════════════════════════════════════
# KPIs PRINCIPAIS
# ══════════════════════════════════════════════════════════════

n_critico = len(df_filtered[df_filtered["Urgência"] == "🔴 CRÍTICO"])
n_alto = len(df_filtered[df_filtered["Urgência"] == "🟠 ALTO"])
n_medio = len(df_filtered[df_filtered["Urgência"] == "🟡 MÉDIO"])
n_baixo = len(df_filtered[df_filtered["Urgência"] == "🟢 BAIXO"])
n_sem = len(df_filtered[df_filtered["Urgência"] == "⚪ SEM DADOS"])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card" style="border-color: #ff4b4b;">
        <div class="metric-label">🔴 CRÍTICO</div>
        <div class="metric-value" style="color: #ff4b4b;">{n_critico}</div>
        <div class="metric-sub">Intervenção imediata</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-color: #ff8c00;">
        <div class="metric-label">🟠 ALTO</div>
        <div class="metric-value" style="color: #ff8c00;">{n_alto}</div>
        <div class="metric-sub">Ação em 24h</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="border-color: #ffd700;">
        <div class="metric-label">🟡 MÉDIO</div>
        <div class="metric-value" style="color: #ffd700;">{n_medio}</div>
        <div class="metric-sub">Monitoramento ativo</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="border-color: #00c851;">
        <div class="metric-label">🟢 BAIXO</div>
        <div class="metric-value" style="color: #00c851;">{n_baixo}</div>
        <div class="metric-sub">Monitoramento padrão</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    pct_risk = round((n_critico + n_alto) / max(len(df_filtered), 1) * 100, 1)
    st.markdown(f"""
    <div class="metric-card" style="border-color: #7c4dff;">
        <div class="metric-label">⚡ TAXA DE RISCO</div>
        <div class="metric-value" style="color: #7c4dff;">{pct_risk}%</div>
        <div class="metric-sub">Crítico + Alto / Total</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# GRÁFICOS — LINHA 1
# ══════════════════════════════════════════════════════════════

g1, g2 = st.columns(2)

with g1:
    st.subheader("📊 Matriz de Risco — Probabilidade × Letra")

    # Heatmap: contagem por Letra x faixa de probabilidade
    df_valid = df_filtered[df_filtered["ProbabilityComplaintInPercent"] >= 0].copy()
    bins = [0, 20, 30, 45, 50, 66, 75, 100]
    labels = ["0-20", "21-30", "31-45", "46-50", "51-66", "67-75", "76-100"]
    df_valid["Faixa"] = pd.cut(df_valid["ProbabilityComplaintInPercent"], bins=bins, labels=labels, include_lowest=True, right=True)

    letter_order = ["A", "B", "C", "D"]
    df_heat = df_valid[df_valid["Letra"].isin(letter_order)]

    if not df_heat.empty:
        heat_pivot = df_heat.groupby(["Letra", "Faixa"], observed=True).size().reset_index(name="Qtd")
        heat_pivot = heat_pivot.pivot(index="Letra", columns="Faixa", values="Qtd").fillna(0).astype(int)
        heat_pivot = heat_pivot.reindex(index=letter_order, fill_value=0)
        heat_pivot = heat_pivot.reindex(columns=labels, fill_value=0)

        fig_heat = px.imshow(
            heat_pivot.values,
            labels=dict(x="Faixa de Probabilidade (%)", y="Letra (Externalização)", color="Pedidos"),
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            color_continuous_scale=["#1a1a2e", "#ff8c00", "#ff4b4b"],
            text_auto=True,
            aspect="auto"
        )
        fig_heat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=30, b=40),
            font=dict(size=13)
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Sem dados válidos para o heatmap.")

with g2:
    st.subheader("🎯 Distribuição por Urgência")

    urgency_counts = df_filtered["Urgência"].value_counts().reset_index()
    urgency_counts.columns = ["Urgência", "Qtd"]

    color_map = {
        "🔴 CRÍTICO": "#ff4b4b",
        "🟠 ALTO": "#ff8c00",
        "🟡 MÉDIO": "#ffd700",
        "🟢 BAIXO": "#00c851",
        "⚪ SEM DADOS": "#555555"
    }

    fig_donut = px.pie(
        urgency_counts,
        values="Qtd",
        names="Urgência",
        color="Urgência",
        color_discrete_map=color_map,
        hole=0.55
    )
    fig_donut.update_traces(textposition="outside", textinfo="label+value+percent", textfont_size=12)
    fig_donut.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# GRÁFICOS — LINHA 2
# ══════════════════════════════════════════════════════════════

g3, g4 = st.columns(2)

with g3:
    st.subheader("📈 Distribuição de Probabilidade (%)")

    df_prob = df_filtered[df_filtered["ProbabilityComplaintInPercent"] >= 0]
    if not df_prob.empty:
        fig_hist = px.histogram(
            df_prob,
            x="ProbabilityComplaintInPercent",
            color="Letra",
            nbins=20,
            color_discrete_map={"A": "#00c851", "B": "#ffd700", "C": "#ff8c00", "D": "#ff4b4b", "Sem Classificação": "#555"},
            barmode="stack",
            labels={"ProbabilityComplaintInPercent": "Probabilidade (%)", "count": "Pedidos"}
        )
        fig_hist.add_vline(x=66, line_dash="dash", line_color="#ff4b4b", annotation_text="Limiar Crítico (66%)")
        fig_hist.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with g4:
    st.subheader("📅 Volume Diário por Urgência")

    if "CreationDate" in df_filtered.columns and df_filtered["CreationDate"].notna().any():
        df_daily = df_filtered[df_filtered["CreationDate"].notna()].copy()
        df_daily["Dia"] = df_daily["CreationDate"].dt.date

        daily_counts = df_daily.groupby(["Dia", "Urgência"]).size().reset_index(name="Qtd")

        fig_line = px.bar(
            daily_counts,
            x="Dia",
            y="Qtd",
            color="Urgência",
            color_discrete_map=color_map,
            barmode="stack",
            labels={"Qtd": "Pedidos", "Dia": "Data"}
        )
        fig_line.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Coluna de data não disponível.")

# ══════════════════════════════════════════════════════════════
# GRÁFICO — SCATTER: RISCO BIDIMENSIONAL
# ══════════════════════════════════════════════════════════════

st.subheader("🗺️ Mapa Bidimensional de Risco — Cada ponto é um pedido")

df_scatter = df_filtered[(df_filtered["ProbabilityComplaintInPercent"] >= 0) & (df_filtered["Letra"].isin(["A","B","C","D"]))].copy()

if not df_scatter.empty:
    letter_num = {"A": 1, "B": 2, "C": 3, "D": 4}
    df_scatter["Letra_Num"] = df_scatter["Letra"].map(letter_num)

    # Jitter para não sobrepor pontos
    np.random.seed(42)
    df_scatter["Prob_Jitter"] = df_scatter["ProbabilityComplaintInPercent"] + np.random.uniform(-2, 2, len(df_scatter))
    df_scatter["Letra_Jitter"] = df_scatter["Letra_Num"] + np.random.uniform(-0.15, 0.15, len(df_scatter))

    fig_scatter = px.scatter(
        df_scatter,
        x="Prob_Jitter",
        y="Letra_Jitter",
        color="Urgência",
        color_discrete_map=color_map,
        hover_data={"OrderId": True, "ProbabilityComplaintInPercent": True, "Letra": True, "Urgência": True, "Prob_Jitter": False, "Letra_Jitter": False},
        labels={"Prob_Jitter": "Probabilidade de Reclamação (%)", "Letra_Jitter": "Risco de Externalização"},
        opacity=0.6
    )

    # Zona crítica
    fig_scatter.add_shape(type="rect", x0=66, x1=100, y0=3.5, y1=4.5, fillcolor="rgba(255,75,75,0.1)", line=dict(color="#ff4b4b", dash="dash"))
    fig_scatter.add_annotation(x=83, y=4.45, text="ZONA CRÍTICA", showarrow=False, font=dict(color="#ff4b4b", size=11, family="Arial Black"))

    fig_scatter.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=60, r=20, t=30, b=60),
        yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=["A - Improvável", "B - Possível", "C - Provável", "D - Muito Provável"]),
        xaxis=dict(range=[-5, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TABELA DE PEDIDOS PRIORITÁRIOS
# ══════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("📋 Lista de Pedidos Prioritários")

# Tabs por urgência
tab_crit, tab_alto, tab_medio, tab_todos = st.tabs(["🔴 Críticos", "🟠 Alto Risco", "🟡 Médio Risco", "📄 Todos os Filtrados"])

display_cols = ["OrderId", "ProbabilityComplaintInPercent", "Letra", "Urgência", "Ação Recomendada", "Conclusion"]
if "Data" in df_filtered.columns:
    display_cols.insert(5, "Data")

rename_map = {
    "OrderId": "Pedido",
    "ProbabilityComplaintInPercent": "Prob. (%)",
    "Letra": "Letra",
    "Urgência": "Urgência",
    "Ação Recomendada": "Ação Recomendada",
    "Data": "Data Criação",
    "Conclusion": "Conclusão IA"
}

available_cols = [c for c in display_cols if c in df_filtered.columns]

with tab_crit:
    df_crit = df_filtered[df_filtered["Urgência"] == "🔴 CRÍTICO"][available_cols].rename(columns=rename_map)
    if df_crit.empty:
        st.success("✅ Nenhum pedido crítico nos filtros atuais!")
    else:
        st.error(f"🚨 **{len(df_crit)} pedidos precisam de intervenção IMEDIATA**")
        st.dataframe(df_crit, use_container_width=True, height=400)

with tab_alto:
    df_alto_tab = df_filtered[df_filtered["Urgência"] == "🟠 ALTO"][available_cols].rename(columns=rename_map)
    if df_alto_tab.empty:
        st.success("✅ Nenhum pedido de alto risco nos filtros atuais!")
    else:
        st.warning(f"⚠️ **{len(df_alto_tab)} pedidos precisam de ação em 24h**")
        st.dataframe(df_alto_tab, use_container_width=True, height=400)

with tab_medio:
    df_medio_tab = df_filtered[df_filtered["Urgência"] == "🟡 MÉDIO"][available_cols].rename(columns=rename_map)
    if df_medio_tab.empty:
        st.info("Nenhum pedido de risco médio nos filtros atuais.")
    else:
        st.info(f"📋 **{len(df_medio_tab)} pedidos em monitoramento ativo**")
        st.dataframe(df_medio_tab, use_container_width=True, height=400)

with tab_todos:
    df_todos = df_filtered[available_cols].rename(columns=rename_map)
    st.info(f"📊 **{len(df_todos)} pedidos no filtro atual**")
    st.dataframe(df_todos, use_container_width=True, height=500)

# ══════════════════════════════════════════════════════════════
# DETALHAMENTO DE PEDIDO INDIVIDUAL
# ══════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("🔎 Detalhamento de Pedido Individual")

order_list = df_filtered["OrderId"].unique().tolist()

if order_list:
    # Se buscou por OrderId, pré-selecionar
    default_idx = 0
    if search_order.strip():
        matches = [i for i, o in enumerate(order_list) if search_order.strip() in str(o)]
        if matches:
            default_idx = matches[0]

    selected_order = st.selectbox("Selecione o pedido:", order_list, index=default_idx)

    row = df_filtered[df_filtered["OrderId"] == selected_order].iloc[0]

    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric("Pedido", f"#{int(row['OrderId'])}")
        st.metric("Probabilidade SRO", f"{row['ProbabilityComplaintInPercent']}%")

    with d2:
        st.metric("Classificação", row["Letra"])
        st.metric("Urgência", row["Urgência"])

    with d3:
        if "Data" in row and pd.notna(row.get("Data")):
            st.metric("Data", row["Data"])
        st.metric("Combinação", row.get("Combinação", "—"))

    st.info(f"**Ação Recomendada:** {row['Ação Recomendada']}")

    if pd.notna(row.get("Conclusion")):
        with st.expander("📄 Conclusão Completa da IA", expanded=False):
            st.write(row["Conclusion"])

    if pd.notna(row.get("ClassificationJustification")):
        with st.expander("📝 Justificativa da Classificação", expanded=False):
            st.write(row["ClassificationJustification"])

    if pd.notna(row.get("PercentJustification")):
        with st.expander("📊 Justificativa do Percentual", expanded=False):
            st.write(row["PercentJustification"])

# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#5a6785; font-size:12px;">'
    'SRO Risk Analyzer Dashboard — Desenvolvido para priorização inteligente de pedidos com risco de reclamação'
    '</p>',
    unsafe_allow_html=True
)
