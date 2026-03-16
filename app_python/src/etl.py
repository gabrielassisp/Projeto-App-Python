"""
etl.py — Extração, transformação e carga dos dados de vendas.

Busca dados da Fake Store API, transforma e salva no banco SQLite.
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
import random

from src.database import SessionLocal, engine
from src.models import Base, Produto, Venda

logger = logging.getLogger(__name__)

API_URL = "https://fakestoreapi.com"


def extrair_produtos() -> list[dict]:
    """Busca todos os produtos da API."""
    logger.info("Buscando produtos da Fake Store API...")
    response = requests.get(f"{API_URL}/products", timeout=10)
    response.raise_for_status()
    produtos = response.json()
    logger.info(f"{len(produtos)} produtos extraídos.")
    return produtos


def transformar_produtos(dados_brutos: list[dict]) -> pd.DataFrame:
    """Limpa e transforma os dados de produtos."""
    df = pd.DataFrame(dados_brutos)

    # Renomear colunas para português
    df = df.rename(columns={
        "id": "id",
        "title": "nome",
        "price": "preco",
        "description": "descricao",
        "category": "categoria",
        "rating": "avaliacao_raw",
    })

    # Extrair nota e contagem da avaliação (campo aninhado)
    df["nota"] = df["avaliacao_raw"].apply(lambda x: x.get("rate", 0) if isinstance(x, dict) else 0)
    df["num_avaliacoes"] = df["avaliacao_raw"].apply(lambda x: x.get("count", 0) if isinstance(x, dict) else 0)
    df = df.drop(columns=["avaliacao_raw"])

    # Garantir tipos corretos
    df["preco"] = df["preco"].astype(float).round(2)
    df["nota"] = df["nota"].astype(float).round(1)
    df["num_avaliacoes"] = df["num_avaliacoes"].astype(int)

    logger.info(f"Transformação concluída: {len(df)} produtos válidos.")
    return df


def gerar_vendas_simuladas(ids_produtos: list[int], n_dias: int = 90) -> pd.DataFrame:
    """
    Gera vendas simuladas para os últimos N dias.
    Em produção, isso seria substituído por dados reais de um ERP ou API.
    """
    logger.info(f"Gerando vendas simuladas para {n_dias} dias...")
    random.seed(42)

    registros = []
    hoje = datetime.now().date()

    # Simular sazonalidade: fins de semana vendem mais
    for i in range(n_dias):
        data = hoje - timedelta(days=i)
        dia_semana = data.weekday()
        fator = 1.6 if dia_semana >= 5 else 1.0  # fim de semana

        n_vendas = int(random.gauss(12, 3) * fator)
        n_vendas = max(1, n_vendas)

        for _ in range(n_vendas):
            produto_id = random.choice(ids_produtos)
            quantidade = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 12, 8, 5])[0]
            registros.append({
                "produto_id": produto_id,
                "quantidade": quantidade,
                "data_venda": data,
            })

    df = pd.DataFrame(registros)
    logger.info(f"{len(df)} registros de vendas gerados.")
    return df


def carregar_banco(df_produtos: pd.DataFrame, df_vendas: pd.DataFrame) -> None:
    """Persiste os dados no banco SQLite."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        # Limpar tabelas antes de recarregar (upsert simples)
        session.query(Venda).delete()
        session.query(Produto).delete()
        session.commit()

        # Inserir produtos
        produtos_obj = [
            Produto(
                id=row["id"],
                nome=row["nome"],
                preco=row["preco"],
                categoria=row["categoria"],
                nota=row["nota"],
                num_avaliacoes=row["num_avaliacoes"],
            )
            for _, row in df_produtos.iterrows()
        ]
        session.bulk_save_objects(produtos_obj)

        # Inserir vendas (calcular receita aqui)
        mapa_preco = df_produtos.set_index("id")["preco"].to_dict()
        vendas_obj = [
            Venda(
                produto_id=row["produto_id"],
                quantidade=row["quantidade"],
                receita=round(row["quantidade"] * mapa_preco.get(row["produto_id"], 0), 2),
                data_venda=row["data_venda"],
            )
            for _, row in df_vendas.iterrows()
        ]
        session.bulk_save_objects(vendas_obj)
        session.commit()

    logger.info(f"Banco atualizado: {len(produtos_obj)} produtos, {len(vendas_obj)} vendas.")


def rodar_etl() -> None:
    """Ponto de entrada principal do pipeline ETL."""
    logger.info("=== Iniciando pipeline ETL ===")
    try:
        dados_brutos = extrair_produtos()
        df_produtos = transformar_produtos(dados_brutos)
        ids_produtos = df_produtos["id"].tolist()
        df_vendas = gerar_vendas_simuladas(ids_produtos)
        carregar_banco(df_produtos, df_vendas)
        logger.info("=== ETL concluído com sucesso ===")
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar a API: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no ETL: {e}")
        raise
