"""Carga: crea el modelo en estrella en SQLite y lo llena con los datos transformados."""
import sqlite3
from contextlib import closing
from pathlib import Path

from config import DB_PATH, METADATA, SERIES
from transform import transformar_todas

SCHEMA_SQL = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def clave_fecha(f):
    return int(f.strftime("%Y%m%d"))


def construir_dim_fecha(tabla):
    fechas = tabla["fecha"].drop_duplicates().sort_values()
    return [
        (clave_fecha(f), f.strftime("%Y-%m-%d"), f.year, (f.month - 1) // 3 + 1,
         f.month, f.day, f.isoweekday())
        for f in fechas
    ]


def cargar():
    tabla, _ = transformar_todas()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    ids = {nombre: i for i, nombre in enumerate(SERIES, start=1)}

    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))

        with con:   # una sola transacción: o se carga todo o nada
            con.executemany(
                "INSERT INTO dim_fecha VALUES (?, ?, ?, ?, ?, ?, ?)",
                construir_dim_fecha(tabla),
            )
            con.executemany(
                "INSERT INTO dim_indicador VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (ids[n], n, METADATA[n]["descripcion"], METADATA[n]["unidad"],
                     METADATA[n]["frecuencia"], codigo)
                    for n, codigo in SERIES.items()
                ],
            )
            con.executemany(
                "INSERT INTO fact_valor VALUES (?, ?, ?)",
                [
                    (clave_fecha(f), ids[ind], float(v))
                    for ind, f, v in tabla[["indicador", "fecha", "valor"]].itertuples(index=False)
                ],
            )

        for t in ("dim_fecha", "dim_indicador", "fact_valor"):
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"{t}: {n} filas")

        print("\nÚltimos 3 valores del dólar (consulta con JOIN):")
        for fila in con.execute("""
            SELECT f.fecha, i.nombre, v.valor
            FROM fact_valor v
            JOIN dim_fecha f USING (fecha_id)
            JOIN dim_indicador i USING (indicador_id)
            WHERE i.nombre = 'dolar'
            ORDER BY f.fecha DESC
            LIMIT 3
        """):
            print(fila)


if __name__ == "__main__":
    cargar()