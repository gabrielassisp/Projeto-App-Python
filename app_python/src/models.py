"""
models.py — Definição das tabelas do banco de dados via SQLAlchemy ORM.
"""

from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class Produto(Base):
    """Tabela de produtos do catálogo."""
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True)
    nome = Column(String(300), nullable=False)
    preco = Column(Float, nullable=False)
    categoria = Column(String(100), nullable=False)
    nota = Column(Float)
    num_avaliacoes = Column(Integer)

    vendas = relationship("Venda", back_populates="produto")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome={self.nome[:30]}, preco={self.preco})>"


class Venda(Base):
    """Tabela de registros de vendas."""
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    receita = Column(Float, nullable=False)
    data_venda = Column(Date, nullable=False)

    produto = relationship("Produto", back_populates="vendas")

    def __repr__(self):
        return f"<Venda(produto_id={self.produto_id}, receita={self.receita}, data={self.data_venda})>"
