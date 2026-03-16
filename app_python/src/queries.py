"""
queries.py — Consultas analíticas ao banco de dados.

Centraliza toda a lógica de acesso a dados para o dashboard.
Separar queries do dashboard facilita testes e manutenção.
"""

import pandas as pd
from sqlalchemy import text
from src.database import engine


def receita_por_dia(dias: int = 30) -> pd.DataFrame:
    """Retorna receita total e número de vendas por dia (últimos N dias)."""
    sql = text("""
        SELECT
            data_venda,
            SUM(receita)    AS receita_total,
            SUM(quantidade) AS unidades_vendidas,
            COUNT(*)        AS num_pedidos
        FROM vendas
        WHERE data_venda >= DATE('now', :offset)
        GROUP BY data_venda
        ORDER BY data_venda
    """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"offset": f"-{dias} days"})
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    return df


def receita_por_categoria() -> pd.DataFrame:
    """Retorna receita, unidades e ticket médio por categoria."""
    sql = text("""
        SELECT
            p.categoria,
            SUM(v.receita)          AS receita_total,
            SUM(v.quantidade)       AS unidades_vendidas,
            COUNT(v.id)             AS num_pedidos,
            ROUND(SUM(v.receita) / COUNT(v.id), 2) AS ticket_medio
        FROM vendas v
        JOIN produtos p ON p.id = v.produto_id
        GROUP BY p.categoria
        ORDER BY receita_total DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def top_produtos(n: int = 10) -> pd.DataFrame:
    """Retorna os N produtos com maior receita."""
    sql = text("""
        SELECT
            p.nome,
            p.categoria,
            p.preco,
            p.nota,
            SUM(v.receita)    AS receita_total,
            SUM(v.quantidade) AS unidades_vendidas
        FROM vendas v
        JOIN produtos p ON p.id = v.produto_id
        GROUP BY p.id
        ORDER BY receita_total DESC
        LIMIT :n
    """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"n": n})
    # Truncar nomes longos para exibição
    df["nome_curto"] = df["nome"].str[:40] + df["nome"].apply(lambda x: "..." if len(x) > 40 else "")
    return df


def kpis_gerais() -> dict:
    """Retorna os principais KPIs para os cards do dashboard."""
    sql = text("""
        SELECT
            ROUND(SUM(receita), 2)          AS receita_total,
            SUM(quantidade)                  AS unidades_vendidas,
            COUNT(DISTINCT produto_id)       AS produtos_ativos,
            COUNT(*)                         AS total_pedidos,
            ROUND(SUM(receita) / COUNT(*), 2) AS ticket_medio
        FROM vendas
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    return {
        "receita_total": row[0] or 0,
        "unidades_vendidas": row[1] or 0,
        "produtos_ativos": row[2] or 0,
        "total_pedidos": row[3] or 0,
        "ticket_medio": row[4] or 0,
    }


def receita_semana_atual_vs_anterior() -> dict:
    """Compara receita da semana atual com a semana anterior (para delta %)."""
    sql = text("""
        SELECT
            SUM(CASE WHEN data_venda >= DATE('now', '-7 days')  THEN receita ELSE 0 END) AS semana_atual,
            SUM(CASE WHEN data_venda >= DATE('now', '-14 days')
                      AND data_venda <  DATE('now', '-7 days')   THEN receita ELSE 0 END) AS semana_anterior
        FROM vendas
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    atual = row[0] or 0
    anterior = row[1] or 1  # evitar divisão por zero
    delta_pct = round((atual - anterior) / anterior * 100, 1)
    return {"semana_atual": atual, "semana_anterior": anterior, "delta_pct": delta_pct}
