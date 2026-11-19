-- Modelo en estrella: una tabla de hechos y dos dimensiones.
-- Se recrea completo en cada ejecución (carga completa, idempotente).

DROP TABLE IF EXISTS fact_valor;
DROP TABLE IF EXISTS dim_indicador;
DROP TABLE IF EXISTS dim_fecha;

CREATE TABLE dim_fecha (
    fecha_id    INTEGER PRIMARY KEY,   -- formato AAAAMMDD, ej. 20240102
    fecha       TEXT NOT NULL UNIQUE,  -- AAAA-MM-DD
    anio        INTEGER NOT NULL,
    trimestre   INTEGER NOT NULL,
    mes         INTEGER NOT NULL,
    dia         INTEGER NOT NULL,
    dia_semana  INTEGER NOT NULL       -- 1 = lunes ... 7 = domingo
);

CREATE TABLE dim_indicador (
    indicador_id INTEGER PRIMARY KEY,
    nombre       TEXT NOT NULL UNIQUE,
    descripcion  TEXT NOT NULL,
    unidad       TEXT NOT NULL,
    frecuencia   TEXT NOT NULL,
    codigo_bcch  TEXT NOT NULL
);

CREATE TABLE fact_valor (
    fecha_id     INTEGER NOT NULL REFERENCES dim_fecha (fecha_id),
    indicador_id INTEGER NOT NULL REFERENCES dim_indicador (indicador_id),
    valor        REAL NOT NULL,
    PRIMARY KEY (fecha_id, indicador_id)
);