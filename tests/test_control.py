import sqlite3
from contextlib import closing

import pytest

import control
import main
from extract import ErrorExtraccion
from load import SCHEMA_SQL


def consulta(db, sql, params=()):
    with closing(sqlite3.connect(db)) as con:
        return con.execute(sql, params).fetchall()


@pytest.fixture
def db(tmp_path, monkeypatch):
    ruta = tmp_path / "prueba.db"
    monkeypatch.setattr(control, "DB_PATH", ruta)
    monkeypatch.setattr(main, "DB_PATH", ruta)
    return ruta


def cargar_modelo_minimo(ruta):
    """Crea el modelo en estrella con 2 fechas del dólar y 1 de la UF."""
    with closing(sqlite3.connect(ruta)) as con, con:
        con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        con.executemany("INSERT INTO dim_fecha VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (20240102, "2024-01-02", 2024, 1, 1, 2, 2),
            (20240103, "2024-01-03", 2024, 1, 1, 3, 3),
        ])
        con.executemany("INSERT INTO dim_indicador VALUES (?, ?, ?, ?, ?, ?)", [
            (1, "dolar", "Dólar", "CLP", "Diaria", "F073.TCO.PRE.Z.D"),
            (2, "uf", "UF", "CLP", "Diaria", "F073.UFF.PRE.Z.D"),
        ])
        con.executemany("INSERT INTO fact_valor VALUES (?, ?, ?)", [
            (20240102, 1, 950.0), (20240103, 1, 955.0), (20240102, 2, 36800.0),
        ])


def test_ejecucion_exitosa_queda_registrada(db):
    eid = control.iniciar_ejecucion("local")
    assert consulta(db, "SELECT estado FROM meta_ejecucion WHERE ejecucion_id = ?", (eid,)) == [("EN_CURSO",)]
    control.finalizar_ejecucion(eid, "EXITO", filas=3, duracion_seg=1.26)
    estado, filas, duracion, fin = consulta(
        db, "SELECT estado, filas_cargadas, duracion_seg, fin FROM meta_ejecucion")[0]
    assert (estado, filas, duracion) == ("EXITO", 3, 1.3)
    assert fin is not None


def test_error_se_registra_con_etapa_y_serie(db):
    eid = control.iniciar_ejecucion("local")
    control.registrar_error(eid, "extraccion", ErrorExtraccion("F073.UFF.PRE.Z.D: sin datos"))
    etapa, indicador, mensaje = consulta(db, "SELECT etapa, indicador, mensaje FROM log_errores")[0]
    assert etapa == "extraccion"
    assert indicador == "uf"
    assert "sin datos" in mensaje


def test_error_no_filtra_el_token(db, monkeypatch):
    monkeypatch.setenv("BCCH_TOKEN", "abc123SECRETO")
    eid = control.iniciar_ejecucion("local")
    control.registrar_error(eid, "extraccion", Exception("fallo en url ...?token=otro999&x=1 con abc123SECRETO"))
    mensaje = consulta(db, "SELECT mensaje FROM log_errores")[0][0]
    assert "abc123SECRETO" not in mensaje
    assert "otro999" not in mensaje


def test_registro_sobrevive_a_la_recarga_del_modelo(db):
    eid = control.iniciar_ejecucion("local")
    control.registrar_error(eid, "transformacion_carga", "falló")
    cargar_modelo_minimo(db)          # aplica schema.sql, que borra y recrea el modelo
    assert consulta(db, "SELECT COUNT(*) FROM log_errores") == [(1,)]
    assert consulta(db, "SELECT COUNT(*) FROM meta_ejecucion") == [(1,)]


def test_actualizar_series_guarda_ultima_fecha_y_filas(db):
    eid = control.iniciar_ejecucion("local")
    cargar_modelo_minimo(db)
    control.actualizar_series(eid)
    filas = dict((f[0], f[1:]) for f in consulta(
        db, "SELECT indicador, ultima_fecha, filas FROM meta_serie"))
    assert filas == {"dolar": ("2024-01-03", 2), "uf": ("2024-01-02", 1)}
    control.actualizar_series(eid)     # repetirlo actualiza, no duplica
    assert consulta(db, "SELECT COUNT(*) FROM meta_serie") == [(2,)]


def test_ejecucion_cortada_se_marca_interrumpida(db):
    primera = control.iniciar_ejecucion("local")      # nunca se finaliza
    segunda = control.iniciar_ejecucion("local")
    estados = dict(consulta(db, "SELECT ejecucion_id, estado FROM meta_ejecucion"))
    assert estados[primera] == "INTERRUMPIDA"
    assert estados[segunda] == "EN_CURSO"


def test_pipeline_fallido_deja_el_error_registrado(db, monkeypatch):
    def falla():
        raise ErrorExtraccion("F073.TCO.PRE.Z.D: Invalid username or password")
    monkeypatch.setattr(main, "extraer_todas", falla)

    with pytest.raises(ErrorExtraccion):
        main.ejecutar()

    assert consulta(db, "SELECT estado FROM meta_ejecucion") == [("ERROR",)]
    etapa, indicador = consulta(db, "SELECT etapa, indicador FROM log_errores")[0]
    assert (etapa, indicador) == ("extraccion", "dolar")


def test_pipeline_exitoso_actualiza_la_metadata(db, monkeypatch):
    monkeypatch.setattr(main, "extraer_todas", lambda: {})
    monkeypatch.setattr(main, "cargar", lambda: cargar_modelo_minimo(db))
    monkeypatch.setattr(main, "crear_vistas", lambda con: None)

    main.ejecutar()

    estado, filas = consulta(db, "SELECT estado, filas_cargadas FROM meta_ejecucion")[0]
    assert (estado, filas) == ("EXITO", 3)
    assert consulta(db, "SELECT COUNT(*) FROM meta_serie") == [(2,)]
    assert consulta(db, "SELECT COUNT(*) FROM log_errores") == [(0,)]
