"""
test_etl.py — Testes unitários para as funções de ETL.

Execute com:
    pytest tests/ -v
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.etl import transformar_produtos, gerar_vendas_simuladas


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def dados_brutos_validos():
    """Simula resposta da Fake Store API com 3 produtos."""
    return [
        {
            "id": 1,
            "title": "Produto Alpha",
            "price": 29.99,
            "description": "Descrição do produto alpha.",
            "category": "electronics",
            "rating": {"rate": 4.5, "count": 120},
        },
        {
            "id": 2,
            "title": "Produto Beta",
            "price": 9.95,
            "description": "Descrição do produto beta.",
            "category": "clothing",
            "rating": {"rate": 3.8, "count": 55},
        },
        {
            "id": 3,
            "title": "Produto Gamma com nome muito longo aqui",
            "price": 149.00,
            "description": "Descrição gamma.",
            "category": "jewelery",
            "rating": {"rate": 4.1, "count": 200},
        },
    ]


# ── Testes de transformação ───────────────────────────────────────────────────

class TestTransformarProdutos:

    def test_retorna_dataframe(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert isinstance(df, pd.DataFrame)

    def test_numero_de_linhas(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert len(df) == 3

    def test_colunas_presentes(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        colunas_esperadas = {"id", "nome", "preco", "categoria", "nota", "num_avaliacoes"}
        assert colunas_esperadas.issubset(set(df.columns))

    def test_preco_arredondado(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        # preço deve ter no máximo 2 casas decimais
        for preco in df["preco"]:
            assert round(preco, 2) == preco

    def test_nota_extraida_do_rating(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert df.loc[df["id"] == 1, "nota"].values[0] == 4.5
        assert df.loc[df["id"] == 2, "nota"].values[0] == 3.8

    def test_num_avaliacoes_extraido(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert df.loc[df["id"] == 1, "num_avaliacoes"].values[0] == 120

    def test_rating_raw_removido(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert "avaliacao_raw" not in df.columns

    def test_tipos_corretos(self, dados_brutos_validos):
        df = transformar_produtos(dados_brutos_validos)
        assert df["preco"].dtype == float
        assert df["nota"].dtype == float
        assert df["num_avaliacoes"].dtype == int

    def test_lista_vazia_retorna_df_vazio(self):
        df = transformar_produtos([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


# ── Testes de geração de vendas ───────────────────────────────────────────────

class TestGerarVendasSimuladas:

    def test_retorna_dataframe(self):
        df = gerar_vendas_simuladas([1, 2, 3], n_dias=7)
        assert isinstance(df, pd.DataFrame)

    def test_colunas_presentes(self):
        df = gerar_vendas_simuladas([1, 2, 3], n_dias=7)
        assert {"produto_id", "quantidade", "data_venda"}.issubset(set(df.columns))

    def test_produto_ids_validos(self):
        ids = [1, 2, 3]
        df = gerar_vendas_simuladas(ids, n_dias=10)
        assert df["produto_id"].isin(ids).all()

    def test_quantidade_positiva(self):
        df = gerar_vendas_simuladas([1, 2], n_dias=10)
        assert (df["quantidade"] > 0).all()

    def test_n_dias_respeitado(self):
        from datetime import datetime, timedelta
        df = gerar_vendas_simuladas([1], n_dias=15)
        hoje = datetime.now().date()
        limite = hoje - timedelta(days=15)
        datas = pd.to_datetime(df["data_venda"]).dt.date
        assert (datas >= limite).all()

    def test_determinismo_com_seed(self):
        """Mesma seed deve gerar mesmos dados."""
        df1 = gerar_vendas_simuladas([1, 2, 3], n_dias=10)
        df2 = gerar_vendas_simuladas([1, 2, 3], n_dias=10)
        assert df1.shape == df2.shape
        assert (df1["quantidade"].values == df2["quantidade"].values).all()
