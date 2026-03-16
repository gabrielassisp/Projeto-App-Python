# Sales Dashboard — ETL Automatizado + Dashboard Interativo

Dashboard de análise de vendas com pipeline ETL automatizado, banco de dados SQLite e interface interativa em Streamlit.

> **Projeto de portfólio** — demonstra boas práticas de engenharia de dados: separação de responsabilidades, ORM, testes unitários, agendamento de jobs e deploy em nuvem.

---

## Contexto

Uma loja online precisa monitorar suas vendas em tempo real, identificar os produtos mais rentáveis e comparar o desempenho entre categorias. Este dashboard responde perguntas como:

- Qual foi a receita dos últimos 30 dias?
- Quais categorias geram mais receita?
- Quais produtos têm o maior volume de vendas?
- A semana atual está melhor ou pior que a anterior?

---

## Arquitetura

```
Fake Store API
      │
      ▼
  src/etl.py          ← Extração, transformação e carga
      │
      ▼
  SQLite (ORM)        ← src/models.py + src/database.py
      │
      ▼
  src/queries.py      ← Consultas analíticas (SQL + pandas)
      │
      ▼
  app.py              ← Dashboard Streamlit
```

O `scheduler.py` executa o ETL automaticamente a cada 60 minutos em background.

---

## Como rodar localmente

### 1. Clonar e instalar

```bash
git clone <repo-url>
cd sales-dashboard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# edite .env se quiser mudar o caminho do banco
```

### 3. Rodar o dashboard

```bash
streamlit run app.py
```

Na primeira execução, o ETL roda automaticamente e popula o banco.

### 4. (Opcional) Rodar o agendador em background

```bash
python -m src.scheduler
```

---

## Testes

```bash
pytest tests/ -v
```

Os testes cobrem as funções de transformação e geração de dados do ETL — sem depender de banco ou API externa.

---

## Estrutura de Pastas

```
sales-dashboard/
├── app.py              # Dashboard principal (Streamlit)
├── src/
│   ├── __init__.py
│   ├── etl.py          # Pipeline ETL
│   ├── models.py       # Modelos SQLAlchemy (ORM)
│   ├── database.py     # Configuração da conexão
│   ├── queries.py      # Consultas analíticas
│   └── scheduler.py    # Agendamento do ETL
├── tests/
│   └── test_etl.py     # Testes unitários
├── notebooks/          # EDA exploratória (Jupyter)
├── data/               # Banco SQLite (gerado automaticamente)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Deploy (Streamlit Community Cloud)

1. Faça push do projeto para um repositório público no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte o repo
3. Configure `DATABASE_URL` nos segredos do Streamlit Cloud
4. Deploy automático em cada push para `main`

---

## Decisões Técnicas

| SQLite + SQLAlchemy ORM | Sem necessidade de servidor externo; ORM facilita manutenção e futura migração para Postgres |
| `schedule` em vez de cron | Portabilidade — roda igual em Windows, Linux e Mac sem configuração extra |
| Queries em `src/queries.py` | Separar acesso a dados do dashboard facilita testes e reuso |
| `python-dotenv` | Credenciais nunca ficam hardcoded no código |
| `@st.cache_data(ttl=300)` | Evita queries repetidas ao banco a cada re-render do Streamlit |
| Testes sem banco | `unittest.mock` permite testar a lógica pura de transformação sem side effects |

---

## Fonte dos Dados

- **Produtos**: [Fake Store API](https://fakestoreapi.com) — API REST pública com produtos, categorias e avaliações
- **Vendas**: Simuladas com distribuição realista (sazonalidade de fim de semana, skew de quantidade)
