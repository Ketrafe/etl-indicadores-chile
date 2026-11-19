import json

import pandas as pd
import pytest

import transform


def escribir_raw(carpeta, nombre, obs):
    (carpeta / f"{nombre}.json").write_text(
        json.dumps({"Codigo": 0, "Series": {"Obs": obs}}), encoding="utf-8"
    )


def tabla(filas):
    return pd.DataFrame(filas, columns=["indicador", "fecha", "valor"])


def test_descarta_filas_sin_dato_y_convierte_tipos(tmp_path, monkeypatch):
    monkeypatch.setattr(transform, "RAW_DIR", tmp_path)
    escribir_raw(tmp_path, "dolar", [
        {"indexDateString": "05-01-2024", "value": "884.45", "statusCode": "OK"},
        {"indexDateString": "06-01-2024", "value": "NaN", "statusCode": "ND"},
        {"indexDateString": "08-01-2024", "value": "893.07", "statusCode": "OK"},
    ])

    df, descartadas = transform.limpiar_serie("dolar")

    assert len(df) == 2
    assert descartadas == 1
    assert df["valor"].dtype == "float64"
    assert df["fecha"].tolist() == [pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-08")]


def test_la_fecha_se_lee_como_dia_mes_anio(tmp_path, monkeypatch):
    monkeypatch.setattr(transform, "RAW_DIR", tmp_path)
    escribir_raw(tmp_path, "uf", [
        {"indexDateString": "02-01-2024", "value": "36805.92", "statusCode": "OK"},
    ])

    df, _ = transform.limpiar_serie("uf")

    assert df["fecha"].iloc[0] == pd.Timestamp("2024-01-02")  # 2 de enero, no 1 de febrero


def test_validar_rechaza_fechas_duplicadas():
    df = tabla([
        ("dolar", pd.Timestamp("2024-01-02"), 877.1),
        ("dolar", pd.Timestamp("2024-01-02"), 877.1),
    ])
    with pytest.raises(ValueError, match="duplicadas"):
        transform.validar(df)


def test_validar_rechaza_valores_no_positivos():
    df = tabla([("dolar", pd.Timestamp("2024-01-02"), -5.0)])
    with pytest.raises(ValueError, match="no positivos"):
        transform.validar(df)


def test_validar_acepta_variacion_negativa_del_ipc():
    df = tabla([("ipc_var_mensual", pd.Timestamp("2024-01-01"), -0.5)])
    transform.validar(df)  # no debe lanzar error