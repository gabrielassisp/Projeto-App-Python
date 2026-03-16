"""
scheduler.py — Agendamento automático do pipeline ETL.

Executa o ETL a cada hora em background.
Em produção, isso seria substituído por Airflow, Prefect ou cron.

Uso:
    python -m src.scheduler
"""

import logging
import time
import schedule

from src.etl import rodar_etl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def job():
    """Função executada pelo agendador."""
    try:
        rodar_etl()
    except Exception as e:
        logger.error(f"ETL falhou: {e}")


if __name__ == "__main__":
    logger.info("Agendador iniciado. ETL rodará a cada 60 minutos.")

    # Rodar imediatamente na inicialização
    job()

    # Agendar execuções periódicas
    schedule.every(60).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)
