-- ============================================================================
-- Fix manual: mover produccion del PID temporal E-4835 (id 603446) al PID real
-- 6939326 (id 603500).
--
-- Caso:
--   Daily web     29422 y 29423  -> woID = 603446 (E-4835)
--   DailyMob      1154 y 1229    -> woID = 603446 (E-4835)
--   No hay produccion en 603500 (6939326).
--
-- Causa:
--   updateLinkOrder solo trasladaba Daily (web), no DailyMob (movil).
--
-- IMPORTANTE:
--   No ejecutar desde la aplicacion. Ejecutar manualmente primero en local y
--   despues en el servidor.
--
-- Docker (desde la raiz del proyecto):
--   docker exec -i wiringconnectionadmin-db-1 psql -U rootuser -d dbname \
--     -v ON_ERROR_STOP=1 < scripts/fix_production_6939326.sql
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- ----------------------------------------------------------------------------
-- 0) Verificacion previa
-- ----------------------------------------------------------------------------
\echo '--- ANTES: produccion por orden ---'
SELECT wo.id,
       wo."prismID",
       wo."Status",
       wo."linkedOrder",
       (SELECT count(*) FROM "workOrder_daily" d WHERE d."woID" = wo.id) AS dailies,
       (SELECT count(*) FROM "mobile_dailymob" m WHERE m."woID" = wo.id) AS dailymob
FROM "workOrder_workorder" wo
WHERE wo.id IN (603446, 603500)
ORDER BY wo.id;

-- Bloqueo de las ordenes y dailies para evitar cambios concurrentes.
SELECT id
FROM "workOrder_workorder"
WHERE id IN (603446, 603500)
FOR UPDATE;

SELECT id
FROM "workOrder_daily"
WHERE id IN (29422, 29423)
FOR UPDATE;

SELECT id
FROM "mobile_dailymob"
WHERE id IN (1154, 1229)
FOR UPDATE;

-- ----------------------------------------------------------------------------
-- 1) Mover Daily web 29422 y 29423 de E-4835 a 6939326
-- ----------------------------------------------------------------------------
UPDATE "workOrder_daily"
SET "woID" = 603500
WHERE id IN (29422, 29423)
  AND "woID" = 603446;

-- ----------------------------------------------------------------------------
-- 2) Mover DailyMob 1154 y 1229 de E-4835 a 6939326
-- ----------------------------------------------------------------------------
UPDATE "mobile_dailymob"
SET "woID" = 603500
WHERE id IN (1154, 1229)
  AND "woID" = 603446;

-- ----------------------------------------------------------------------------
-- 3) Sincronizar estados de las ordenes
--
--    603500 queda Ready to Bill (7) porque la produccion ya estaba aprobada.
--    603446 (E-4835) vuelve a Not Started (1) y se limpian ubicacion,
--    supervisor y usuario/fecha de asignacion.
--
--    Si NO se desea modificar estados, comentar todo el bloque 3.
-- ----------------------------------------------------------------------------

-- 3a) 603500 -> Ready to Bill (7), con registro en woStatusLog.
WITH before AS (
    SELECT id, "Status" AS old_status
    FROM "workOrder_workorder"
    WHERE id = 603500
),
updated AS (
    UPDATE "workOrder_workorder" w
    SET "Status" = '7'
    FROM before b
    WHERE w.id = b.id
      AND w."Status" IS DISTINCT FROM '7'
    RETURNING w.id
)
INSERT INTO "workOrder_wostatuslog"
    ("woID", "currentStatus", "nextStatus", "created_date", "createdBy")
SELECT u.id, b.old_status, '7', now(), 'manual_fix'
FROM updated u
JOIN before b ON b.id = u.id;

-- 3b) 603446 (E-4835) -> Not Started (1), con registro en woStatusLog.
WITH before AS (
    SELECT id, "Status" AS old_status
    FROM "workOrder_workorder"
    WHERE id = 603446
),
updated AS (
    UPDATE "workOrder_workorder" w
    SET "Status" = '1'
    FROM before b
    WHERE w.id = b.id
      AND w."Status" IS DISTINCT FROM '1'
    RETURNING w.id
)
INSERT INTO "workOrder_wostatuslog"
    ("woID", "currentStatus", "nextStatus", "created_date", "createdBy")
SELECT u.id, b.old_status, '1', now(), 'manual_fix'
FROM updated u
JOIN before b ON b.id = u.id;

-- 3c) Limpiar campos de asignacion de E-4835 (sin produccion).
UPDATE "workOrder_workorder"
SET "Location_id" = NULL,
    "WCSup" = NULL,
    "UploadDate" = NULL,
    "UserName" = NULL
WHERE id = 603446;

-- ----------------------------------------------------------------------------
-- 4) Verificacion posterior
-- ----------------------------------------------------------------------------
\echo '--- DESPUES: produccion por orden ---'
SELECT wo.id,
       wo."prismID",
       wo."Status",
       wo."linkedOrder",
       (SELECT count(*) FROM "workOrder_daily" d WHERE d."woID" = wo.id) AS dailies,
       (SELECT count(*) FROM "mobile_dailymob" m WHERE m."woID" = wo.id) AS dailymob
FROM "workOrder_workorder" wo
WHERE wo.id IN (603446, 603500)
ORDER BY wo.id;

\echo '--- DESPUES: dailies web afectados ---'
SELECT id, "woID", day, crew, "mobile_id"
FROM "workOrder_daily"
WHERE id IN (29422, 29423)
ORDER BY id;

\echo '--- DESPUES: dailies moviles afectados ---'
SELECT id, "woID", day, crew, "Status"
FROM "mobile_dailymob"
WHERE id IN (1154, 1229)
ORDER BY id;

COMMIT;
