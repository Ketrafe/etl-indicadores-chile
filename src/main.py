"""Orquestador: ejecuta el pipeline completo (extraer, transformar, cargar y
crear vistas) y registra cada etapa."""
import logging
import sqlite3
import sys
import time
from contextlib import closing

from analisis import crear_vistas
from config import DB_PATH
from extract import ErrorExtraccion, extraer_todas
from load import cargar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("pipeline")


def ejecutar():
    inicio = time.time()
    log.info("Inicio del pipeline")

    log.info("1/3 Extracción desde la API del Banco Central")
    extraer_todas()

    log.info("2/3 Transformación y carga al modelo en estrella")
    cargar()

    log.info("3/3 Creación de vistas SQL")
    with closing(sqlite3.connect(DB_PATH)) as con:
        crear_vistas(con)
        hechos = con.execute("SELECT COUNT(*) FROM fact_valor").fetchone()[0]

    log.info("Pipeline terminado en %.1f s: %s valores en fact_valor", time.time() - inicio, hechos)


if __name__ == "__main__":
    try:
        ejecutar()
    except ErrorExtraccion as e:
        log.error("Falló la extracción: %s", e)
        sys.exit(1)
    except Exception:
        log.exception("Falló el pipeline")
        sys.exit(1)