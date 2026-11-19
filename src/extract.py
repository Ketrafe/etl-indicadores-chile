"""Extracción: descarga las series desde la API del Banco Central y guarda
la respuesta original sin modificar (capa raw)."""
import json
import os
from datetime import date

import requests
from dotenv import load_dotenv

from config import API_URL, FECHA_INICIO, RAW_DIR, SERIES

load_dotenv()


class ErrorExtraccion(Exception):
    """La API respondió, pero no con los datos esperados."""


def extraer_serie(codigo, desde, hasta):
    token = os.getenv("BCCH_TOKEN")
    if not token:
        raise ErrorExtraccion("Falta BCCH_TOKEN en el archivo .env")

    params = {
        "token": token,
        "function": "GetSeries",
        "timeseries": codigo,
        "firstdate": desde,
        "lastdate": hasta,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=60)
        resp.raise_for_status()
        datos = resp.json()
    except (requests.RequestException, ValueError) as e:
        # "from None" evita que el error original, que incluye la URL con el token, se muestre
        raise ErrorExtraccion(
            f"{codigo}: fallo de conexión o respuesta inválida ({type(e).__name__})"
        ) from None

    if datos.get("Codigo") != 0:
        raise ErrorExtraccion(f"{codigo}: {datos.get('Descripcion')}")
    if not (datos.get("Series") or {}).get("Obs"):
        raise ErrorExtraccion(f"{codigo}: la API respondió sin observaciones")
    return datos


def extraer_todas(desde=FECHA_INICIO, hasta=None):
    hasta = hasta or date.today().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for nombre, codigo in SERIES.items():
        datos = extraer_serie(codigo, desde, hasta)
        ruta = RAW_DIR / f"{nombre}.json"
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{nombre}: {len(datos['Series']['Obs'])} observaciones -> {ruta}")


if __name__ == "__main__":
    extraer_todas()