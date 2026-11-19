import pandas as pd

from load import clave_fecha, construir_dim_fecha


def test_clave_fecha_tiene_formato_aaaammdd():
    assert clave_fecha(pd.Timestamp("2024-01-02")) == 20240102


def test_dim_fecha_calcula_atributos_de_calendario():
    tabla = pd.DataFrame({"fecha": [pd.Timestamp("2024-11-19")]})

    (fila,) = construir_dim_fecha(tabla)

    # (fecha_id, fecha, año, trimestre, mes, día, día de la semana: 2 = martes)
    assert fila == (20241119, "2024-11-19", 2024, 4, 11, 19, 2)