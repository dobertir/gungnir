-- 001_schema_v1.sql
-- Schema migration v1: adds empresas and adjudicaciones tables.
--
-- Safe to run multiple times (idempotent via CREATE TABLE IF NOT EXISTS).
-- Does NOT drop or modify the existing proyectos, leads, or _sync_log tables.
-- Run this before running the backfill queries documented in context/schema_v1.md.
--
-- Order:
--   1. empresas  — one row per unique rut_beneficiario
--   2. adjudicaciones — one row per (rut_beneficiario, año_adjudicacion)
--   3. Indexes for common query patterns

-- ── empresas ──────────────────────────────────────────────────────────────────
-- Entidad canónica de empresa. Derivada de proyectos durante el sync mensual.
-- Nunca sobrescribir datos de leads a partir de esta tabla.
CREATE TABLE IF NOT EXISTS empresas (
    rut_beneficiario             TEXT PRIMARY KEY,
    razon_social_canonical       TEXT NOT NULL,
    sector_economico             TEXT,
    region_ejecucion_principal   TEXT,
    tramo_ventas                 TEXT,
    inicio_actividad             TEXT,               -- TEXT 'YYYY-MM-DD', may be NULL
    total_proyectos              INTEGER NOT NULL DEFAULT 0,
    monto_total_aprobado_corfo   REAL    NOT NULL DEFAULT 0.0,  -- CLP, aggregated
    primera_adjudicacion         INTEGER,            -- earliest año_adjudicacion
    ultima_adjudicacion          INTEGER,            -- most recent año_adjudicacion
    tipo_persona_beneficiario    TEXT,
    created_at                   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── adjudicaciones ────────────────────────────────────────────────────────────
-- Granularity: empresa x año. Aggregated from proyectos during sync.
-- aprobado_corfo (TEXT in proyectos) is cast to REAL before storing here.
-- "año_adjudicacion" must be double-quoted because of the ñ character.
CREATE TABLE IF NOT EXISTS adjudicaciones (
    rut_beneficiario    TEXT    NOT NULL,
    "año_adjudicacion"  INTEGER NOT NULL,
    proyectos_count     INTEGER NOT NULL DEFAULT 0,
    monto_corfo         REAL    NOT NULL DEFAULT 0.0,  -- SUM(CAST(aprobado_corfo AS REAL))
    monto_privado       REAL    NOT NULL DEFAULT 0.0,  -- SUM(CAST(aprobado_privado AS REAL))
    monto_ley           REAL    NOT NULL DEFAULT 0.0,  -- SUM(CAST(monto_consolidado_ley AS REAL))
    sectores            TEXT,                          -- comma-separated unique sectors (GROUP_CONCAT(DISTINCT))
    instrumentos        TEXT,                          -- comma-separated unique instrumento_homologado
    PRIMARY KEY (rut_beneficiario, "año_adjudicacion")
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
-- empresas: JOINs from leads and adjudicaciones, and frequent filter columns
CREATE INDEX IF NOT EXISTS idx_empresas_rut
    ON empresas (rut_beneficiario);

CREATE INDEX IF NOT EXISTS idx_empresas_sector
    ON empresas (sector_economico);

CREATE INDEX IF NOT EXISTS idx_empresas_region
    ON empresas (region_ejecucion_principal);

CREATE INDEX IF NOT EXISTS idx_empresas_tramo
    ON empresas (tramo_ventas);

-- adjudicaciones: temporal queries and company lookups
CREATE INDEX IF NOT EXISTS idx_adj_rut
    ON adjudicaciones (rut_beneficiario);

CREATE INDEX IF NOT EXISTS idx_adj_anio
    ON adjudicaciones ("año_adjudicacion");
