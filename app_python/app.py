"""
app.py — Dashboard de Vendas interativo com Streamlit.

Ponto de entrada principal. Execute com:
    streamlit run app.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

from src.queries import (
    receita_por_dia,
    receita_por_categoria,
    top_produtos,
    kpis_gerais,
    receita_semana_atual_vs_anterior,
)
from src.etl import rodar_etl

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS customizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 8px;
    }
    .metric-label { font-size: 12px; color: #6c7086; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #cdd6f4; margin: 4px 0; }
    .metric-delta-pos { font-size: 13px; color: #a6e3a1; }
    .metric-delta-neg { font-size: 13px; color: #f38ba8; }
    div[data-testid="stSidebar"] { background: #181825; }
    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = {
    "plot_bgcolor": "#1e1e2e",
    "paper_bgcolor": "#1e1e2e",
    "font_color": "#cdd6f4",
}
GRID_COLOR = "#313244"
CORES_CATEGORIAS = px.colors.qualitative.Pastel


# ── Funções auxiliares ───────────────────────────────────────────────────────

def formatar_moeda(valor: float) -> str:
    return f"$ {valor:,.2f}"


def card_kpi(label: str, valor: str, delta: str = "", positivo: bool = True):
    delta_class = "metric-delta-pos" if positivo else "metric-delta-neg"
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{valor}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Configurações")
    st.divider()

    dias_historico = st.slider("Janela histórica (dias)", min_value=7, max_value=90, value=30, step=7)

    st.divider()
    st.subheader("🔄Atualizar Dados")
    st.caption("Executa o pipeline ETL manualmente para buscar dados frescos da API.")
    if st.button("Rodar ETL agora", use_container_width=True, type="primary"):
        with st.spinner("Executando pipeline..."):
            try:
                rodar_etl()
                st.success("ETL concluído com sucesso!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro no ETL: {e}")

    st.divider()
    st.caption("Fonte: [Fake Store API](https://fakestoreapi.com)")
    st.caption("Vendas: simuladas com sazonalidade (90 dias)")


# ── Cache das queries ────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # cache de 5 minutos
def load_kpis():
    return kpis_gerais()

@st.cache_data(ttl=300)
def load_delta():
    return receita_semana_atual_vs_anterior()

@st.cache_data(ttl=300)
def load_por_dia(dias):
    return receita_por_dia(dias)

@st.cache_data(ttl=300)
def load_por_categoria():
    return receita_por_categoria()

@st.cache_data(ttl=300)
def load_top_produtos(n):
    return top_produtos(n)


# ── Verificar se banco existe ────────────────────────────────────────────────
db_path = Path("data/vendas.db")
if not db_path.exists():
    st.info("Banco de dados não encontrado. Rodando ETL inicial...")
    with st.spinner("Isso pode levar alguns segundos..."):
        rodar_etl()
    st.rerun()


# ── Título ───────────────────────────────────────────────────────────────────
st.title("Sales Dashboard")
st.caption(f"Exibindo dados dos últimos **{dias_historico} dias**  •  Atualização automática a cada 5 min")
st.divider()


# ── KPI Cards ────────────────────────────────────────────────────────────────
kpis = load_kpis()
delta = load_delta()
delta_str = f"{'▲' if delta['delta_pct'] >= 0 else '▼'} {abs(delta['delta_pct'])}% vs semana anterior"

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    card_kpi("Receita Total", formatar_moeda(kpis["receita_total"]),
             delta_str, delta["delta_pct"] >= 0)
with col2:
    card_kpi("Pedidos", f"{kpis['total_pedidos']:,}")
with col3:
    card_kpi("Unidades Vendidas", f"{kpis['unidades_vendidas']:,}")
with col4:
    card_kpi("Ticket Médio", formatar_moeda(kpis["ticket_medio"]))
with col5:
    card_kpi("Produtos Ativos", str(kpis["produtos_ativos"]))


st.divider()


# ── Gráfico de Receita ao Longo do Tempo ─────────────────────────────────────
df_dia = load_por_dia(dias_historico)

st.subheader("Receita Diária")

if not df_dia.empty:
    # Média móvel de 7 dias
    df_dia["media_movel_7d"] = df_dia["receita_total"].rolling(7, min_periods=1).mean()

    fig_linha = go.Figure()
    fig_linha.add_trace(go.Scatter(
        x=df_dia["data_venda"], y=df_dia["receita_total"],
        name="Receita diária",
        mode="lines",
        line=dict(color="#89b4fa", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(137,180,250,0.08)",
    ))
    fig_linha.add_trace(go.Scatter(
        x=df_dia["data_venda"], y=df_dia["media_movel_7d"],
        name="Média móvel 7 dias",
        mode="lines",
        line=dict(color="#a6e3a1", width=2, dash="dot"),
    ))
    fig_linha.update_layout(
        **PLOTLY_THEME,
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=GRID_COLOR, tickprefix="$ "),
        hovermode="x unified",
    )
    st.plotly_chart(fig_linha, use_container_width=True)
else:
    st.warning("Sem dados de vendas para o período selecionado.")


# ── Linha 2: Categorias + Top Produtos ──────────────────────────────────────
col_a, col_b = st.columns([1, 1.4])

with col_a:
    st.subheader("Receita por Categoria")
    df_cat = load_por_categoria()
    if not df_cat.empty:
        fig_pizza = px.pie(
            df_cat,
            values="receita_total",
            names="categoria",
            hole=0.5,
            color_discrete_sequence=CORES_CATEGORIAS,
        )
        fig_pizza.update_traces(
            textposition="outside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Receita: $%{value:,.2f}<br>Participação: %{percent}",
        )
        fig_pizza.update_layout(
            **PLOTLY_THEME,
            showlegend=False,
            height=340,
            margin=dict(l=20, r=20, t=10, b=10),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

with col_b:
    st.subheader("Top 10 Produtos")
    n_top = st.selectbox("Exibir top:", [5, 10, 15], index=1, label_visibility="collapsed")
    df_top = load_top_produtos(n_top)
    if not df_top.empty:
        fig_bar = px.bar(
            df_top.sort_values("receita_total"),
            x="receita_total",
            y="nome_curto",
            orientation="h",
            color="categoria",
            color_discrete_sequence=CORES_CATEGORIAS,
            labels={"receita_total": "Receita ($)", "nome_curto": ""},
        )
        fig_bar.update_layout(
            **PLOTLY_THEME,
            height=340,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            xaxis=dict(tickprefix="$ ", gridcolor=GRID_COLOR),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ── Tabela de categorias ─────────────────────────────────────────────────────
st.divider()
st.subheader("Detalhamento por Categoria")

df_cat_tabela = load_por_categoria().copy()
df_cat_tabela["receita_total"] = df_cat_tabela["receita_total"].apply(formatar_moeda)
df_cat_tabela["ticket_medio"] = df_cat_tabela["ticket_medio"].apply(formatar_moeda)
df_cat_tabela = df_cat_tabela.rename(columns={
    "categoria": "Categoria",
    "receita_total": "Receita Total",
    "unidades_vendidas": "Unidades",
    "num_pedidos": "Pedidos",
    "ticket_medio": "Ticket Médio",
})
st.dataframe(df_cat_tabela, use_container_width=True, hide_index=True)
