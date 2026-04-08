"""
database.py — Configuração do banco de dados SQLite.

Usa /tmp no Streamlit Cloud (filesystem read-only) e
a pasta local do projeto em qualquer outro ambiente.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Caminho do banco ──────────────────────────────────────────────────────────
# O Streamlit Cloud monta o código em /mount/src e só permite escrita em /tmp.
# Em ambiente local, salva o banco na pasta src/ do projeto.

_IS_STREAMLIT_CLOUD = os.path.exists("/mount/src")
_DB_DIR = "/tmp" if _IS_STREAMLIT_CLOUD else os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{_DB_DIR}/vendas.db"
DB_PATH = f"{_DB_DIR}/vendas.db"

# ── Engine e sessão ───────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Base declarativa (única para todo o projeto) ──────────────────────────────
class Base(DeclarativeBase):
    pass
