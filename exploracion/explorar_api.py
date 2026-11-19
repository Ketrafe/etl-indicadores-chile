"""Exploración de la API del Banco Central: pide unos días del dólar
observado y muestra la respuesta tal cual la entrega el servidor."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()                        # lee el archivo .env
TOKEN = os.getenv("BCCH_TOKEN")      # el token nunca se escribe en el código

URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
params = {
    "token": TOKEN,
    "function": "GetSeries",
    "timeseries": "F073.TCO.PRE.Z.D",    # dólar observado, serie diaria
    "firstdate": "2024-01-01",
    "lastdate": "2024-01-10",
}

resp = requests.get(URL, params=params, timeout=30)
print("Código HTTP:", resp.status_code)
print(resp.text[:1500])