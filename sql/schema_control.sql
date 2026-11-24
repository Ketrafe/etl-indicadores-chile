-- Tablas de control del pipeline. A diferencia de schema.sql (que recrea el modelo
-- en cada ejecución), estas NO se borran: conservan el historial entre corridas.
-- Las horas se guardan en UTC.

-- Una fila por ejecución del pipeline.
CREATE TABLE IF NOT EXISTS meta_ejecucion (
    ejecucion_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio         TEXT NOT NULL,
    fin            TEXT,
    duracion_seg   REAL,
    estado         TEXT NOT NULL CHECK (estado IN ('EN_CURSO', 'EXITO', 'ERROR', 'INTERRUMPIDA')),
    filas_cargadas INTEGER,
    origen         TEXT NOT NULL
);

-- Una fila por serie: hasta qué fecha hay datos y qué ejecución los cargó.
CREATE TABLE IF NOT EXISTS meta_serie (
    indicador           TEXT PRIMARY KEY,
    codigo_bcch         TEXT NOT NULL,
    ultima_fecha        TEXT,
    filas               INTEGER,
    ultima_ejecucion_id INTEGER REFERENCES meta_ejecucion (ejecucion_id),
    actualizado_en      TEXT
);

-- Una fila por error, con la etapa y la serie afectada.
CREATE TABLE IF NOT EXISTS log_errores (
    error_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER REFERENCES meta_ejecucion (ejecucion_id),
    fecha_hora   TEXT NOT NULL,
    etapa        TEXT NOT NULL,
    indicador    TEXT,
    mensaje      TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_ultimas_ejecuciones AS
SELECT e.ejecucion_id, e.inicio, e.estado, e.duracion_seg, e.filas_cargadas, e.origen,
       (SELECT COUNT(*) FROM log_errores l WHERE l.ejecucion_id = e.ejecucion_id) AS errores
FROM meta_ejecucion e
ORDER BY e.ejecucion_id DESC;
