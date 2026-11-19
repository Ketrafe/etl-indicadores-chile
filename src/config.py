"""Configuración del pipeline: fuente, series y rutas."""
from pathlib import Path

API_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

# nombre interno -> código de serie del Banco Central
SERIES = {
    "dolar": "F073.TCO.PRE.Z.D",              # dólar observado (CLP/USD), diario
    "uf": "F073.UFF.PRE.Z.D",                 # unidad de fomento, diaria
    "utm": "F073.UTR.PRE.Z.M",                # unidad tributaria mensual
    "ipc_indice": "G073.IPC.IND.2023.M",      # IPC general, índice base 2023=100, mensual
    "ipc_var_mensual": "G073.IPC.VAR.2023.M", # IPC general, variación mensual oficial
}

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/indicadores.db")
FECHA_INICIO = "2020-01-01"