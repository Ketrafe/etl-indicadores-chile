"""Control del pipeline: registro de ejecuciones, metadatos por serie y log de errores.

Las tablas viven en la misma base SQLite (sql/schema_control.sql) y se escriben en
conexiones y transacciones propias: si la carga falla y se revierte, el registro del
error se conserva.

Uso (desde la carpeta del proyecto):  python src/control.py
"""
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH, SERIES

SCHEMA_CONTROL = Path(__file__).resolve().parent.parent / "sql" / "schema_control.sql"
MAX_MENSAJE = 500


def _ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def conectar(db_path=None):
    """Abre la base y se asegura de que existan las tablas de control."""
    ruta = Path(db_path or DB_PATH)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA_CONTROL.read_text(encoding="utf-8"))
    return con


def origen():
    return "github_actions" if os.getenv("GITHUB_ACTIONS") == "true" else "local"


def limpiar(texto):
    """Quita secretos de un mensaje antes de guardarlo: el valor de cualquier variable
    BCCH_* y los parámetros token/pass/user de una URL."""
    texto = str(texto)
    for nombre, valor in os.environ.items():
        if nombre.startswith("BCCH_") and len(valor) >= 6:
            texto = texto.replace(valor, "***")
    texto = re.sub(r"(?i)\b(token|pass|password|user)=[^&\s'\")]+", r"\1=***", texto)
    return texto[:MAX_MENSAJE]


def _detectar_indicador(texto):
    for nombre, codigo in SERIES.items():
        if codigo in texto:
            return nombre
    return None


def iniciar_ejecucion(origen_ejecucion=None, db_path=None):
    """Registra una ejecución nueva y devuelve su id. Si quedó alguna 'EN_CURSO' de una
    corrida anterior, el proceso se cortó antes de terminar: se marca INTERRUMPIDA."""
    with closing(conectar(db_path)) as con, con:
        con.execute("UPDATE meta_ejecucion SET estado = 'INTERRUMPIDA' WHERE estado = 'EN_CURSO'")
        cur = con.execute(
            "INSERT INTO meta_ejecucion (inicio, estado, origen) VALUES (?, 'EN_CURSO', ?)",
            (_ahora(), origen_ejecucion or origen()),
        )
        return cur.lastrowid


def finalizar_ejecucion(ejecucion_id, estado, filas=None, duracion_seg=None, db_path=None):
    with closing(conectar(db_path)) as con, con:
        con.execute(
            "UPDATE meta_ejecucion SET fin = ?, duracion_seg = ?, estado = ?, filas_cargadas = ? "
            "WHERE ejecucion_id = ?",
            (_ahora(), None if duracion_seg is None else round(duracion_seg, 1), estado, filas, ejecucion_id),
        )


def registrar_error(ejecucion_id, etapa, error, indicador=None, db_path=None):
    """Guarda un error. 'error' puede ser una excepción o un texto."""
    if isinstance(error, BaseException):
        texto = f"{type(error).__name__}: {error}"
    else:
        texto = str(error)
    texto = limpiar(texto)
    with closing(conectar(db_path)) as con, con:
        con.execute(
            "INSERT INTO log_errores (ejecucion_id, fecha_hora, etapa, indicador, mensaje) "
            "VALUES (?, ?, ?, ?, ?)",
            (ejecucion_id, _ahora(), etapa, indicador or _detectar_indicador(texto), texto),
        )


def actualizar_series(ejecucion_id, db_path=None):
    """Actualiza meta_serie con lo que hay cargado en el modelo: última fecha y filas por serie."""
    with closing(conectar(db_path)) as con, con:
        con.execute(
            """
            INSERT INTO meta_serie (indicador, codigo_bcch, ultima_fecha, filas, ultima_ejecucion_id, actualizado_en)
            SELECT i.nombre, i.codigo_bcch, MAX(f.fecha), COUNT(*), ?, ?
            FROM fact_valor v
            JOIN dim_fecha f USING (fecha_id)
            JOIN dim_indicador i USING (indicador_id)
            WHERE 1 = 1
            GROUP BY i.indicador_id
            ON CONFLICT (indicador) DO UPDATE SET
                codigo_bcch = excluded.codigo_bcch,
                ultima_fecha = excluded.ultima_fecha,
                filas = excluded.filas,
                ultima_ejecucion_id = excluded.ultima_ejecucion_id,
                actualizado_en = excluded.actualizado_en
            """,
            (ejecucion_id, _ahora()),
        )


def mostrar_estado(n=5, db_path=None):
    """Imprime las últimas ejecuciones, los últimos errores y el estado de cada serie."""
    with closing(conectar(db_path)) as con:
        print("Ultimas ejecuciones (hora UTC):")
        for f in con.execute("SELECT * FROM v_ultimas_ejecuciones LIMIT ?", (n,)):
            print("  ", f)

        print("\nUltimos errores:")
        errores = con.execute(
            "SELECT ejecucion_id, fecha_hora, etapa, indicador, mensaje "
            "FROM log_errores ORDER BY error_id DESC LIMIT ?", (n,)
        ).fetchall()
        for f in errores:
            print("  ", f)
        if not errores:
            print("   (sin errores)")

        print("\nEstado por serie:")
        for f in con.execute(
            "SELECT indicador, ultima_fecha, filas, ultima_ejecucion_id FROM meta_serie ORDER BY indicador"
        ):
            print("  ", f)


if __name__ == "__main__":
    mostrar_estado()
