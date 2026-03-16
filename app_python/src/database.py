"""
database.py — Configuração da conexão com o banco de dados SQLite.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Caminho do banco pode ser configurado via variável de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/vendas.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necessário para SQLite + Streamlit
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
