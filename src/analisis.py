"""Análisis: crea las vistas SQL sobre el modelo en estrella y muestra resultados clave."""
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from config import DB_PATH

VISTAS_SQL = Path(__file__).resolve().parent.parent / "sql" / "vistas.sql"


def crear_vistas(con):
    con.executescript(VISTAS_SQL.read_text(encoding="utf-8"))


def consulta(con, sql):
    return pd.read_sql_query(sql, con)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    with closing(sqlite3.connect(DB_PATH)) as con:
        crear_vistas(con)

        print("1) Dólar: promedio mensual y variación (últimos 6 meses)")
        print(consulta(con, """
            SELECT anio, mes, valor_prom, var_mensual_pct
            FROM v_variacion_mensual
            WHERE indicador = 'dolar'
            ORDER BY anio DESC, mes DESC
            LIMIT 6
        """).to_string(index=False))

        print("\n2) Dólar por año")
        print(consulta(con, """
            SELECT anio,
                   ROUND(AVG(valor), 1) AS promedio,
                   ROUND(MIN(valor), 1) AS minimo,
                   ROUND(MAX(valor), 1) AS maximo
            FROM v_indicadores
            WHERE indicador = 'dolar'
            GROUP BY anio
            ORDER BY anio
        """).to_string(index=False))

        print("\n3) Validación del IPC: calculado desde el índice vs serie oficial")
        print(consulta(con, """
            SELECT COUNT(*)                    AS meses_comparados,
                   MAX(diferencia)             AS diferencia_maxima,
                   SUM(diferencia > 0.05)      AS meses_con_diferencia_mayor_a_0_05
            FROM v_ipc_validacion
        """).to_string(index=False))