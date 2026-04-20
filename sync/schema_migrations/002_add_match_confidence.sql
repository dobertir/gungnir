-- 002_add_match_confidence.sql
-- Idempotent: adds match_confidence column to empresas if it does not already exist.
--
-- SQLite raises "duplicate column name" if ALTER TABLE ADD COLUMN is run a second
-- time — this must be caught by the caller (Python) and silently ignored.
--
-- match_confidence values:
--   1.0        — empresa identificada por RUT (alta confianza)
--   0.85–1.0   — empresa identificada por coincidencia de nombre difuso
--   0.0        — sin resolución posible (nombre vacío, sin RUT)

BEGIN;

ALTER TABLE empresas ADD COLUMN match_confidence REAL DEFAULT 1.0;

COMMIT;
