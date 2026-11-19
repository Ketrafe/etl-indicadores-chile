"""Busca en el catálogo del Banco Central series mensuales cuyo título contenga IPC."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BCCH_TOKEN")
URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

params = {"token": TOKEN, "function": "SearchSeries", "frequency": "MONTHLY"}
datos = requests.get(URL, params=params, timeout=60).json()

print("Respuesta:", datos.get("Codigo"), datos.get("Descripcion"))
series = datos.get("SeriesInfos") or []
print("Series mensuales en el catálogo:", len(series))

if not series:
    print(str(datos)[:1500])
else:
    print("Campos disponibles:", list(series[0].keys()))
    encontradas = [s for s in series if "ipc" in str(s.get("spanishTitle", "")).lower()]
    print("Coinciden con 'IPC':", len(encontradas))
    for s in encontradas[:40]:
        print(s.get("seriesId"), "|", s.get("spanishTitle"), "|",
              s.get("firstObservation"), "->", s.get("lastObservation"))