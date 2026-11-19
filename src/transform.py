"""Transformación: convierte las respuestas JSON del Banco Central en una
tabla limpia y ordenada (formato largo): indicador, fecha, valor."""
import json

import pandas as pd

from config import RAW_DIR, SERIES


def leer_raw(nombre):
    ruta = RAW_DIR / f"{nombre}.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return pd.DataFrame(datos["Series"]["Obs"])


def limpiar_serie(nombre):
    df = leer_raw(nombre)
    total = len(df)

    df["fecha"] = pd.to_datetime(df["indexDateString"], format="%d-%m-%Y")
    df["valor"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[(df["statusCode"] == "OK") & df["valor"].notna()]

    df = df.assign(indicador=nombre)[["indicador", "fecha", "valor"]]
    df = df.drop_duplicates(subset=["indicador", "fecha"]).sort_values("fecha")
    return df, total - len(df)


def validar(df):
    problemas = []
    if df[["indicador", "fecha", "valor"]].isna().any().any():
        problemas.append("hay valores nulos")
    if df.duplicated(subset=["indicador", "fecha"]).any():
        problemas.append("hay fechas duplicadas por indicador")
    positivas = df[df["indicador"].isin(["dolar", "uf", "utm", "ipc_indice"])]
    if (positivas["valor"] <= 0).any():
        problemas.append("hay valores no positivos en series que deben ser positivas")
    if problemas:
        raise ValueError("Validación fallida: " + "; ".join(problemas))


def transformar_todas():
    partes, descartadas = [], {}
    for nombre in SERIES:
        df, n_desc = limpiar_serie(nombre)
        partes.append(df)
        descartadas[nombre] = n_desc
    resultado = pd.concat(partes, ignore_index=True)
    validar(resultado)
    return resultado, descartadas


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    tabla, descartadas = transformar_todas()
    resumen = tabla.groupby("indicador").agg(
        filas=("valor", "size"),
        desde=("fecha", "min"),
        hasta=("fecha", "max"),
        minimo=("valor", "min"),
        maximo=("valor", "max"),
    )
    print(resumen)
    print("\nFilas descartadas (sin dato):", descartadas)