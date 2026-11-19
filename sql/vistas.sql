-- Vistas sobre el modelo en estrella. Se recrean en cada ejecución.

DROP VIEW IF EXISTS v_ipc_validacion;
DROP VIEW IF EXISTS v_variacion_mensual;
DROP VIEW IF EXISTS v_indicadores;

-- 1. Vista plana: une hechos y dimensiones. Es la que consumiría Power BI.
CREATE VIEW v_indicadores AS
SELECT f.fecha,
       f.anio,
       f.trimestre,
       f.mes,
       i.nombre     AS indicador,
       i.unidad,
       i.frecuencia,
       v.valor
FROM fact_valor v
JOIN dim_fecha f USING (fecha_id)
JOIN dim_indicador i USING (indicador_id);

-- 2. Valor promedio mensual y su variación contra el mes anterior.
CREATE VIEW v_variacion_mensual AS
WITH mensual AS (
    SELECT anio, mes, indicador, AVG(valor) AS valor_prom
    FROM v_indicadores
    WHERE indicador IN ('dolar', 'uf', 'utm', 'ipc_indice')
    GROUP BY anio, mes, indicador
)
SELECT anio,
       mes,
       indicador,
       ROUND(valor_prom, 2) AS valor_prom,
       ROUND(100.0 * (valor_prom / LAG(valor_prom) OVER (
                 PARTITION BY indicador ORDER BY anio, mes) - 1), 2) AS var_mensual_pct
FROM mensual;

-- 3. Validación: variación mensual del IPC calculada desde el índice
--    vs la serie oficial de variación del Banco Central.
CREATE VIEW v_ipc_validacion AS
WITH base AS (
    SELECT fecha,
           MAX(CASE WHEN indicador = 'ipc_indice'      THEN valor END) AS indice,
           MAX(CASE WHEN indicador = 'ipc_var_mensual' THEN valor END) AS var_oficial
    FROM v_indicadores
    WHERE indicador IN ('ipc_indice', 'ipc_var_mensual')
    GROUP BY fecha
),
calc AS (
    SELECT fecha, indice, var_oficial,
           100.0 * (indice / LAG(indice) OVER (ORDER BY fecha) - 1) AS var_calculada
    FROM base
)
SELECT fecha,
       ROUND(indice, 3)       AS indice,
       ROUND(var_oficial, 2)  AS var_oficial,
       ROUND(var_calculada, 2) AS var_calculada,
       ROUND(ABS(var_calculada - var_oficial), 2) AS diferencia
FROM calc
WHERE var_calculada IS NOT NULL;