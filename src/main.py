"""Orquestador: ejecuta el pipeline completo (extraer, transformar, cargar y
crear vistas) y registra cada etapa, cada ejecución y cada error en la base."""
import logging
import sqlite3
import sys
import time
from contextlib import closing

import control
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


def _registrar_fallo(ejecucion_id, etapa, error, duracion):
    """Guarda el error y cierra la ejecución. Si la base de control falla, no tapa el error original."""
    try:
        control.registrar_error(ejecucion_id, etapa, error)
        control.finalizar_ejecucion(ejecucion_id, "ERROR", duracion_seg=duracion)
    except Exception:
        log.warning("No se pudo registrar el error en las tablas de control")


def ejecutar():
    inicio = time.time()
    ejecucion_id = control.iniciar_ejecucion()
    log.info("Inicio del pipeline (ejecución %s)", ejecucion_id)

    etapa = "extraccion"
    try:
        log.info("1/3 Extracción desde la API del Banco Central")
        extraer_todas()

        etapa = "transformacion_carga"
        log.info("2/3 Transformación y carga al modelo en estrella")
        cargar()

        etapa = "vistas"
        log.info("3/3 Creación de vistas SQL")
        with closing(sqlite3.connect(DB_PATH)) as con:
            crear_vistas(con)
            hechos = con.execute("SELECT COUNT(*) FROM fact_valor").fetchone()[0]

        etapa = "control"
        control.actualizar_series(ejecucion_id)
    except Exception as error:
        _registrar_fallo(ejecucion_id, etapa, error, time.time() - inicio)
        raise

    duracion = time.time() - inicio
    control.finalizar_ejecucion(ejecucion_id, "EXITO", hechos, duracion)
    log.info("Pipeline terminado en %.1f s: %s valores en fact_valor", duracion, hechos)


if __name__ == "__main__":
    try:
        ejecutar()
    except ErrorExtraccion as e:
        log.error("Falló la extracción: %s", e)
        sys.exit(1)
    except Exception:
        log.exception("Falló el pipeline")
        sys.exit(1)
