"""Verifica que los códigos de serie candidatos existan y muestra qué entregan."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BCCH_TOKEN")
URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

CANDIDATAS = {
    "dolar": "F073.TCO.PRE.Z.D",
    "uf": "F073.UFF.PRE.Z.D",
    "utm": "F073.UTR.PRE.Z.M",
    "ipc": "G073.IPC.IND.2018.M",
}

for nombre, codigo in CANDIDATAS.items():
    params = {
        "token": TOKEN,
        "function": "GetSeries",
        "timeseries": codigo,
        "firstdate": "2024-01-01",
        "lastdate": "2024-03-31",
    }
    datos = requests.get(URL, params=params, timeout=30).json()

    print(f"\n== {nombre} ({codigo}) ==")
    print("Respuesta:", datos.get("Codigo"), datos.get("Descripcion"))
    serie = datos.get("Series") or {}
    if serie.get("Obs"):
        print("Descripción:", serie.get("descripEsp"))
        print("Observaciones:", len(serie["Obs"]))
        print("Primeras dos:", serie["Obs"][:2])