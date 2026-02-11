import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
# PALETA CARGLASS
# ══════════════════════════════════════════════════════════════
CARGLASS_RED = "#D32F2F"
CARGLASS_RED_DARK = "#B71C1C"
CARGLASS_PURPLE = "#7B1FA2"
CARGLASS_PURPLE_BG = "#8E24AA"
CARGLASS_WHITE = "#FFFFFF"
CARGLASS_GRAY_BG = "#F5F5F5"
CARGLASS_GRAY_LIGHT = "#EEEEEE"
CARGLASS_GRAY_TEXT = "#757575"
CARGLASS_DARK_TEXT = "#212121"

# ══════════════════════════════════════════════════════════════
# CSS — PADRÃO CARGLASS (fundo branco, header vermelho, cards roxos)
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    .stApp {{
        background-color: {CARGLASS_WHITE};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {CARGLASS_GRAY_BG};
        border-right: 2px solid {CARGLASS_GRAY_LIGHT};
    }}
    section[data-testid="stSidebar"] * {{
        color: {CARGLASS_DARK_TEXT} !important;
    }}
    .carglass-header {{
        background: linear-gradient(135deg, {CARGLASS_RED} 0%, {CARGLASS_RED_DARK} 100%);
        color: white;
        padding: 20px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }}
    .carglass-header h1 {{
        margin: 0; font-size: 24px; font-weight: 800; color: white;
    }}
    .carglass-header p {{
        margin: 4px 0 0 0; font-size: 13px; color: rgba(255,255,255,0.85);
    }}
    .kpi-card {{
        background: linear-gradient(135deg, {CARGLASS_PURPLE} 0%, {CARGLASS_PURPLE_BG} 100%);
        border-radius: 12px;
        padding: 20px 24px;
        color: white;
        min-height: 120px;
    }}
    .kpi-label {{
        font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.9);
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    }}
    .kpi-value {{
        font-size: 38px; font-weight: 800; color: white; line-height: 1; margin-bottom: 4px;
    }}
    .kpi-sub {{ font-size: 12px; color: rgba(255,255,255,0.7); }}
    .urgency-card {{
        background: white; border-radius: 10px; padding: 16px 20px;
        border-left: 5px solid; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 8px;
    }}
    .urgency-critical {{ border-left-color: {CARGLASS_RED}; }}
    .urgency-high {{ border-left-color: #FF8C00; }}
    .urgency-medium {{ border-left-color: #FFC107; }}
    .urgency-low {{ border-left-color: #4CAF50; }}
    .uc-label {{
        font-size: 12px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: {CARGLASS_GRAY_TEXT};
    }}
    .uc-value {{ font-size: 30px; font-weight: 800; line-height: 1.1; }}
    .uc-sub {{ font-size: 11px; color: {CARGLASS_GRAY_TEXT}; }}
    .section-title {{
        font-size: 18px; font-weight: 700; color: {CARGLASS_DARK_TEXT};
        margin: 24px 0 12px 0; padding-bottom: 8px;
        border-bottom: 2px solid {CARGLASS_RED}; display: inline-block;
    }}
    .stat-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-size: 13px; border-radius: 8px; overflow: hidden;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    }}
    .stat-table th {{
        background: {CARGLASS_RED}; color: white; padding: 10px 14px;
        text-align: left; font-weight: 600; font-size: 12px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }}
    .stat-table td {{
        padding: 10px 14px; border-bottom: 1px solid {CARGLASS_GRAY_LIGHT}; color: {CARGLASS_DARK_TEXT};
    }}
    .stat-table tr:nth-child(even) td {{ background: {CARGLASS_GRAY_BG}; }}
    .stat-table tr:hover td {{ background: #E3F2FD; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 8px 8px 0 0; padding: 8px 20px; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ background-color: {CARGLASS_RED} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# FUNÇÕES
# ══════════════════════════════════════════════════════════════

def normalize_classification(val):
    if pd.isna(val) or str(val).strip() == "":
        return "Sem Classificação"
    val = str(val).strip().upper()
    for letter in ["D", "C", "B", "A"]:
        if letter in val:
            return letter
    return "Sem Classificação"


def classify_urgency(row):
    prob = row["ProbabilityComplaintInPercent"]
    letter = row["Letra"]
    if prob < 0:
        return "⚪ SEM DADOS"
    if letter == "D" and prob >= 50:
        return "🔴 CRÍTICO"
    if letter == "C" and prob >= 66:
        return "🟠 ALTO"
    if letter == "D":
        return "🟠 ALTO"
    if prob >= 70:
        return "🟠 ALTO"
    if letter == "C" and prob >= 45:
        return "🟡 MÉDIO"
    if letter == "B" and prob >= 66:
        return "🟡 MÉDIO"
    if prob >= 50:
        return "🟡 MÉDIO"
    return "🟢 BAIXO"


def urgency_sort_key(val):
    return {"🔴 CRÍTICO": 0, "🟠 ALTO": 1, "🟡 MÉDIO": 2, "🟢 BAIXO": 3, "⚪ SEM DADOS": 4}.get(val, 5)


def get_action(urgency):
    return {
        "🔴 CRÍTICO": "🚨 Intervenção imediata — Contatar em até 2h. Escalar para supervisor.",
        "🟠 ALTO": "⚠️ Ação em 24h — Contato proativo obrigatório. Monitorar canais externos.",
        "🟡 MÉDIO": "📋 Monitoramento ativo — Contato preventivo em 48h recomendado.",
        "🟢 BAIXO": "✅ Monitoramento padrão — Acompanhamento regular.",
        "⚪ SEM DADOS": "❓ Verificar — Dados incompletos, reprocessar análise."
    }.get(urgency, "—")


@st.cache_data(show_spinner=False)
def load_and_process(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Consulta1", engine="openpyxl")
    df["Letra"] = df["Classification"].apply(normalize_classification)
    df["ProbabilityComplaintInPercent"] = pd.to_numeric(df["ProbabilityComplaintInPercent"], errors="coerce").fillna(-1).astype(int)
    df["Urgência"] = df.apply(classify_urgency, axis=1)
    df["_sort"] = df["Urgência"].apply(urgency_sort_key)
    df = df.sort_values(["_sort", "ProbabilityComplaintInPercent"], ascending=[True, False]).drop(columns=["_sort"])
    df["Ação Recomendada"] = df["Urgência"].apply(get_action)
    if "CreationDate" in df.columns:
        df["CreationDate"] = pd.to_datetime(df["CreationDate"], errors="coerce")
        df["Data"] = df["CreationDate"].dt.strftime("%d/%m/%Y %H:%M")
    return df


PLOTLY_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, sans-serif", size=13, color=CARGLASS_DARK_TEXT),
    margin=dict(l=40, r=20, t=40, b=40),
)

URGENCY_COLORS = {
    "🔴 CRÍTICO": CARGLASS_RED,
    "🟠 ALTO": "#FF8C00",
    "🟡 MÉDIO": "#FFC107",
    "🟢 BAIXO": "#4CAF50",
    "⚪ SEM DADOS": "#BDBDBD"
}


# ══════════════════════════════════════════════════════════════
# HEADER CARGLASS
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="carglass-header">
    <h1>🚨 SRO Risk Analyzer</h1>
    <p>Dashboard de Indicadores de Gestão — Priorização de Pedidos com Risco de Reclamação</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════

uploaded_file = st.file_uploader(
    "📎 Anexe o arquivo Excel com os dados de previsão (aba Consulta1)",
    type=["xlsx", "xls"],
    help="O arquivo deve conter a aba 'Consulta1'."
)

if uploaded_file is None:
    st.info("👆 Faça upload do arquivo Excel para iniciar a análise.")
    st.stop()

with st.spinner("⏳ Processando dados..."):
    df = load_and_process(uploaded_file)

total = len(df)
valid = len(df[df["ProbabilityComplaintInPercent"] >= 0])

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f'<h2 style="color:{CARGLASS_RED};">🔧 Filtros</h2>', unsafe_allow_html=True)

    urgency_options = ["🔴 CRÍTICO", "🟠 ALTO", "🟡 MÉDIO", "🟢 BAIXO", "⚪ SEM DADOS"]
    selected_urgency = st.multiselect("Nível de Urgência", urgency_options, default=["🔴 CRÍTICO", "🟠 ALTO", "🟡 MÉDIO"])

    letter_options = sorted(df["Letra"].unique())
    selected_letters = st.multiselect("Classificação (Letra)", letter_options, default=letter_options)

    prob_min, prob_max = st.slider("Faixa de Probabilidade (%)", -1, 100, (0, 100))

    if "CreationDate" in df.columns and df["CreationDate"].notna().any():
        min_date = df["CreationDate"].min().date()
        max_date = df["CreationDate"].max().date()
        date_range = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

    search_order = st.text_input("🔍 Buscar OrderId", placeholder="Ex: 2963358")

    st.markdown("---")
    st.markdown(f"**📊 Resumo do Arquivo**")
    st.markdown(f"- Total: **{total:,}**")
    st.markdown(f"- Válidos: **{valid:,}**")
    st.markdown(f"- Sem dados: **{total - valid:,}**")

# Aplicar filtros
mask = (
    df["Urgência"].isin(selected_urgency) &
    df["Letra"].isin(selected_letters) &
    (df["ProbabilityComplaintInPercent"] >= prob_min) &
    (df["ProbabilityComplaintInPercent"] <= prob_max)
)
if date_range and len(date_range) == 2 and "CreationDate" in df.columns:
    mask &= (df["CreationDate"].dt.date >= date_range[0]) & (df["CreationDate"].dt.date <= date_range[1])
if search_order.strip():
    mask &= df["OrderId"].astype(str).str.contains(search_order.strip())

df_f = df[mask].copy()

# ══════════════════════════════════════════════════════════════
# KPIs ROXOS
# ══════════════════════════════════════════════════════════════

n_crit = len(df_f[df_f["Urgência"] == "🔴 CRÍTICO"])
n_alto = len(df_f[df_f["Urgência"] == "🟠 ALTO"])
n_med = len(df_f[df_f["Urgência"] == "🟡 MÉDIO"])
n_baixo = len(df_f[df_f["Urgência"] == "🟢 BAIXO"])
pct_risk = round((n_crit + n_alto) / max(len(df_f), 1) * 100, 1)
avg_prob = df_f[df_f["ProbabilityComplaintInPercent"] >= 0]["ProbabilityComplaintInPercent"].mean()
avg_prob = round(avg_prob, 1) if not pd.isna(avg_prob) else 0
pct_low = round(n_baixo / max(len(df_f), 1) * 100, 1)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Total de Pedidos</div>
        <div class="kpi-value">{len(df_f):,}</div>
        <div class="kpi-sub">Nos filtros selecionados</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Taxa de Risco (Crítico+Alto)</div>
        <div class="kpi-value">{pct_risk}%</div>
        <div class="kpi-sub">{"⚠️ Acima do aceitável" if pct_risk > 15 else "✓ Dentro do objetivo"}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Risco Baixo</div>
        <div class="kpi-value">{pct_low}%</div>
        <div class="kpi-sub">{"✓ Dentro do objetivo" if pct_low > 70 else "↓ Abaixo do ideal"}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Probabilidade Média</div>
        <div class="kpi-value">{avg_prob}%</div>
        <div class="kpi-sub">Média geral de risco SRO</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# CARDS DE URGÊNCIA
# ══════════════════════════════════════════════════════════════

u1, u2, u3, u4 = st.columns(4)
with u1:
    st.markdown(f"""<div class="urgency-card urgency-critical">
        <div class="uc-label">🔴 Crítico</div>
        <div class="uc-value" style="color:{CARGLASS_RED};">{n_crit}</div>
        <div class="uc-sub">Intervenção imediata</div>
    </div>""", unsafe_allow_html=True)
with u2:
    st.markdown(f"""<div class="urgency-card urgency-high">
        <div class="uc-label">🟠 Alto</div>
        <div class="uc-value" style="color:#FF8C00;">{n_alto}</div>
        <div class="uc-sub">Ação em 24h</div>
    </div>""", unsafe_allow_html=True)
with u3:
    st.markdown(f"""<div class="urgency-card urgency-medium">
        <div class="uc-label">🟡 Médio</div>
        <div class="uc-value" style="color:#F9A825;">{n_med}</div>
        <div class="uc-sub">Monitoramento ativo</div>
    </div>""", unsafe_allow_html=True)
with u4:
    st.markdown(f"""<div class="urgency-card urgency-low">
        <div class="uc-label">🟢 Baixo</div>
        <div class="uc-value" style="color:#4CAF50;">{n_baixo}</div>
        <div class="uc-sub">Monitoramento padrão</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# GRÁFICOS — LINHA 1
# ══════════════════════════════════════════════════════════════

g1, g2 = st.columns([3, 2])

with g1:
    st.markdown('<div class="section-title">📊 Análise por Classificação (Letra)</div>', unsafe_allow_html=True)
    df_valid = df_f[df_f["Letra"].isin(["A", "B", "C", "D"])].copy()
    if not df_valid.empty:
        letter_stats = df_valid.groupby("Letra").agg(
            Qtd=("OrderId", "count"), Media=("ProbabilityComplaintInPercent", "mean")
        ).reindex(["A", "B", "C", "D"]).fillna(0)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=letter_stats.index, y=letter_stats["Qtd"],
            marker_color=CARGLASS_RED, text=letter_stats["Qtd"].astype(int),
            textposition="outside", name="Pedidos"
        ))
        fig_bar.add_trace(go.Scatter(
            x=letter_stats.index, y=letter_stats["Media"],
            mode="lines+markers+text",
            text=[f"{v:.0f}%" for v in letter_stats["Media"]],
            textposition="top center",
            line=dict(color=CARGLASS_PURPLE, width=2, dash="dash"),
            marker=dict(size=8, color=CARGLASS_PURPLE),
            name="Prob. Média (%)", yaxis="y2"
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT, height=380,
            yaxis=dict(title="Quantidade de Pedidos"),
            yaxis2=dict(title="Probabilidade Média (%)", overlaying="y", side="right", range=[0, 100]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with g2:
    st.markdown('<div class="section-title">📋 Estatísticas por Letra</div>', unsafe_allow_html=True)
    if not df_valid.empty:
        stats = df_valid.groupby("Letra").agg(
            Total=("OrderId", "count"), Prob_Media=("ProbabilityComplaintInPercent", "mean"),
        ).reindex(["A", "B", "C", "D"]).fillna(0)
        for letter in ["A", "B", "C", "D"]:
            sub = df_valid[df_valid["Letra"] == letter]
            stats.loc[letter, "Risco_Baixo"] = round(len(sub[sub["Urgência"] == "🟢 BAIXO"]) / max(len(sub), 1) * 100, 0)

        rows_html = ""
        for letter in ["A", "B", "C", "D"]:
            if letter in stats.index:
                r = stats.loc[letter]
                rows_html += f"<tr><td><strong>{letter}</strong></td><td>{int(r['Prob_Media'])}%</td><td>{int(r['Total']):,}</td><td>{int(r['Risco_Baixo'])}%</td></tr>"

        st.markdown(f"""<table class="stat-table">
            <tr><th>Letra</th><th>Prob. Média</th><th>Total Pedidos</th><th>% Risco Baixo</th></tr>
            {rows_html}
        </table>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# GRÁFICOS — LINHA 2
# ══════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)
g3, g4 = st.columns(2)

with g3:
    st.markdown('<div class="section-title">📈 Distribuição de Probabilidade</div>', unsafe_allow_html=True)
    df_prob = df_f[df_f["ProbabilityComplaintInPercent"] >= 0]
    if not df_prob.empty:
        fig_hist = px.histogram(
            df_prob, x="ProbabilityComplaintInPercent", color="Letra", nbins=20,
            color_discrete_map={"A": "#4CAF50", "B": "#FFC107", "C": "#FF8C00", "D": CARGLASS_RED, "Sem Classificação": "#BDBDBD"},
            barmode="stack", labels={"ProbabilityComplaintInPercent": "Probabilidade (%)", "count": "Pedidos"}
        )
        fig_hist.add_vline(x=66, line_dash="dash", line_color=CARGLASS_RED, annotation_text="Limiar 66%", annotation_font_color=CARGLASS_RED)
        fig_hist.update_layout(**PLOTLY_LAYOUT, height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_hist, use_container_width=True)

with g4:
    st.markdown('<div class="section-title">🎯 Distribuição por Urgência</div>', unsafe_allow_html=True)
    urg_counts = df_f["Urgência"].value_counts().reset_index()
    urg_counts.columns = ["Urgência", "Qtd"]
    fig_donut = px.pie(urg_counts, values="Qtd", names="Urgência", color="Urgência",
        color_discrete_map=URGENCY_COLORS, hole=0.55)
    fig_donut.update_traces(textposition="outside", textinfo="label+value+percent", textfont_size=12)
    fig_donut.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False)
    st.plotly_chart(fig_donut, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# GRÁFICOS — LINHA 3
# ══════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)
g5, g6 = st.columns(2)

with g5:
    st.markdown('<div class="section-title">📅 Volume Diário por Urgência</div>', unsafe_allow_html=True)
    if "CreationDate" in df_f.columns and df_f["CreationDate"].notna().any():
        df_daily = df_f[df_f["CreationDate"].notna()].copy()
        df_daily["Dia"] = df_daily["CreationDate"].dt.date
        daily = df_daily.groupby(["Dia", "Urgência"]).size().reset_index(name="Qtd")
        fig_daily = px.bar(daily, x="Dia", y="Qtd", color="Urgência",
            color_discrete_map=URGENCY_COLORS, barmode="stack", labels={"Qtd": "Pedidos", "Dia": "Data"})
        fig_daily.update_layout(**PLOTLY_LAYOUT, height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_daily, use_container_width=True)

with g6:
    st.markdown('<div class="section-title">🗺️ Mapa Bidimensional de Risco</div>', unsafe_allow_html=True)
    df_sc = df_f[(df_f["ProbabilityComplaintInPercent"] >= 0) & (df_f["Letra"].isin(["A","B","C","D"]))].copy()
    if not df_sc.empty:
        letter_num = {"A": 1, "B": 2, "C": 3, "D": 4}
        df_sc["Letra_Num"] = df_sc["Letra"].map(letter_num)
        np.random.seed(42)
        df_sc["Prob_J"] = df_sc["ProbabilityComplaintInPercent"] + np.random.uniform(-2, 2, len(df_sc))
        df_sc["Letra_J"] = df_sc["Letra_Num"] + np.random.uniform(-0.15, 0.15, len(df_sc))
        fig_sc = px.scatter(df_sc, x="Prob_J", y="Letra_J", color="Urgência",
            color_discrete_map=URGENCY_COLORS, opacity=0.5,
            hover_data={"OrderId": True, "ProbabilityComplaintInPercent": True, "Letra": True, "Prob_J": False, "Letra_J": False})
        fig_sc.add_shape(type="rect", x0=66, x1=100, y0=3.5, y1=4.5,
            fillcolor="rgba(211,47,47,0.08)", line=dict(color=CARGLASS_RED, dash="dash"))
        fig_sc.add_annotation(x=83, y=4.45, text="ZONA CRÍTICA", showarrow=False,
            font=dict(color=CARGLASS_RED, size=11, family="Arial Black"))
        fig_sc.update_layout(**PLOTLY_LAYOUT, height=400,
            yaxis=dict(tickvals=[1,2,3,4], ticktext=["A - Improvável","B - Possível","C - Provável","D - Muito Provável"]),
            xaxis=dict(title="Probabilidade (%)", range=[-5, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TABELAS
# ══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown('<div class="section-title">📋 Lista de Pedidos Prioritários</div>', unsafe_allow_html=True)

tab_crit, tab_alto, tab_medio, tab_todos = st.tabs(["🔴 Críticos", "🟠 Alto Risco", "🟡 Médio", "📄 Todos"])

display_cols = ["OrderId", "ProbabilityComplaintInPercent", "Letra", "Urgência", "Ação Recomendada", "Conclusion"]
if "Data" in df_f.columns:
    display_cols.insert(5, "Data")
available = [c for c in display_cols if c in df_f.columns]
renames = {"OrderId": "Pedido", "ProbabilityComplaintInPercent": "Prob. (%)", "Ação Recomendada": "Ação",
           "Data": "Data Criação", "Conclusion": "Conclusão IA"}

with tab_crit:
    dc = df_f[df_f["Urgência"] == "🔴 CRÍTICO"][available].rename(columns=renames)
    if dc.empty:
        st.success("✅ Nenhum pedido crítico nos filtros atuais!")
    else:
        st.error(f"🚨 **{len(dc)} pedidos precisam de intervenção IMEDIATA**")
        st.dataframe(dc, use_container_width=True, height=400)

with tab_alto:
    da = df_f[df_f["Urgência"] == "🟠 ALTO"][available].rename(columns=renames)
    if da.empty:
        st.success("✅ Nenhum pedido de alto risco!")
    else:
        st.warning(f"⚠️ **{len(da)} pedidos precisam de ação em 24h**")
        st.dataframe(da, use_container_width=True, height=400)

with tab_medio:
    dm = df_f[df_f["Urgência"] == "🟡 MÉDIO"][available].rename(columns=renames)
    if dm.empty:
        st.info("Nenhum pedido de risco médio.")
    else:
        st.info(f"📋 **{len(dm)} pedidos em monitoramento ativo**")
        st.dataframe(dm, use_container_width=True, height=400)

with tab_todos:
    dt = df_f[available].rename(columns=renames)
    st.info(f"📊 **{len(dt)} pedidos no filtro atual**")
    st.dataframe(dt, use_container_width=True, height=500)

# ══════════════════════════════════════════════════════════════
# DETALHAMENTO INDIVIDUAL
# ══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown('<div class="section-title">🔎 Detalhamento de Pedido Individual</div>', unsafe_allow_html=True)

order_list = df_f["OrderId"].unique().tolist()
if order_list:
    default_idx = 0
    if search_order.strip():
        matches = [i for i, o in enumerate(order_list) if search_order.strip() in str(o)]
        if matches:
            default_idx = matches[0]

    selected_order = st.selectbox("Selecione o pedido:", order_list, index=default_idx)
    row = df_f[df_f["OrderId"] == selected_order].iloc[0]

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
    f'<p style="text-align:center; color:{CARGLASS_GRAY_TEXT}; font-size:12px;">'
    'SRO Risk Analyzer Dashboard — Priorização inteligente de pedidos com risco de reclamação'
    '</p>', unsafe_allow_html=True)
