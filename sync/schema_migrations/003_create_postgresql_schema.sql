-- 003_create_postgresql_schema.sql
-- Schema DDL completo para PostgreSQL (equivalente a corfo_alimentos.db).
--
-- Uso:
--   psql $DATABASE_URL -f sync/schema_migrations/003_create_postgresql_schema.sql
--
-- Idempotente: seguro de re-ejecutar (CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS).
-- Nota: la nota "002" del issue fue asignada antes de detectar que 001/002 ya existían
-- como migraciones SQLite; este archivo lleva el número siguiente disponible.
--
-- Orden de creación:
--   1. organizations    (referenciada por users)
--   2. users
--   3. proyectos        (tabla principal de datos CORFO)
--   4. empresas         (derivada de proyectos durante sync)
--   5. adjudicaciones   (agregación empresa × año)
--   6. leads            (CRM pipeline)
--   7. _sync_log        (log del sync mensual)
--   8. Índices

-- ── organizations ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizations (
    id         SERIAL      PRIMARY KEY,
    name       TEXT        NOT NULL,
    slug       TEXT        NOT NULL UNIQUE,
    plan       TEXT        NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL      PRIMARY KEY,
    org_id        INTEGER     NOT NULL REFERENCES organizations(id),
    username      TEXT        NOT NULL,
    password_hash TEXT        NOT NULL,
    role          TEXT        NOT NULL DEFAULT 'viewer',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, username)
);

-- ── proyectos ─────────────────────────────────────────────────────────────────
-- Tabla principal de proyectos CORFO. Fuente: datainnovacion.cl/api (sync mensual).
-- aprobado_corfo y otros montos: NUMERIC (TEXT en SQLite legacy, siempre CAST allá).
-- "año_adjudicacion" requiere comillas por la ñ, tanto en DDL como en queries.
CREATE TABLE IF NOT EXISTS proyectos (
    codigo                          TEXT    PRIMARY KEY,
    foco_apoyo                      TEXT,
    tipo_intervencion               TEXT,
    instrumento                     TEXT,
    instrumento_homologado          TEXT,
    estado_data                     TEXT,
    tipo_persona_beneficiario       TEXT,
    rut_beneficiario                TEXT,
    razon                           TEXT,
    titulo_del_proyecto             TEXT,
    objetivo_general_del_proyecto   TEXT,
    "año_adjudicacion"              INTEGER,
    aprobado_corfo                  NUMERIC,
    aprobado_privado                NUMERIC,
    aprobado_privado_pecuniario     NUMERIC,
    monto_consolidado_ley           NUMERIC,
    tipo_innovacion                 TEXT,
    mercado_objetivo_final          TEXT,
    criterio_mujer                  TEXT,
    genero_director                 TEXT,
    sostenible                      TEXT,
    ods_principal_sostenible        TEXT,
    meta_principal_cod              TEXT,
    economia_circular_si_no         TEXT,
    modelo_de_circularidad          TEXT,
    region_ejecucion                TEXT,
    tramo_ventas                    TEXT,
    inicio_actividad                TEXT,
    sector_economico                TEXT,
    patron_principal_asociado       TEXT,
    tipo_proyecto                   TEXT,
    r_principal                     TEXT,
    estrategia_r_principal          TEXT,
    ley_rep_si_no                   TEXT,
    ley_rep                         TEXT,
    ernc                            TEXT,
    tendencia_final                 TEXT
);

-- ── empresas ──────────────────────────────────────────────────────────────────
-- Entidad canónica de empresa. Derivada de proyectos durante el sync mensual.
-- Nunca sobrescribir datos de leads a partir de esta tabla.
CREATE TABLE IF NOT EXISTS empresas (
    rut_beneficiario             TEXT        PRIMARY KEY,
    razon_social_canonical       TEXT        NOT NULL,
    sector_economico             TEXT,
    region_ejecucion_principal   TEXT,
    tramo_ventas                 TEXT,
    inicio_actividad             TEXT,                    -- 'YYYY-MM-DD', puede ser NULL
    total_proyectos              INTEGER     NOT NULL DEFAULT 0,
    monto_total_aprobado_corfo   NUMERIC     NOT NULL DEFAULT 0,  -- CLP, aggregated
    primera_adjudicacion         INTEGER,                 -- earliest año_adjudicacion
    ultima_adjudicacion          INTEGER,                 -- most recent año_adjudicacion
    tipo_persona_beneficiario    TEXT,
    match_confidence             NUMERIC                  DEFAULT 1.0,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── adjudicaciones ────────────────────────────────────────────────────────────
-- Granularidad: empresa × año. Agregado desde proyectos durante sync.
CREATE TABLE IF NOT EXISTS adjudicaciones (
    rut_beneficiario    TEXT    NOT NULL,
    "año_adjudicacion"  INTEGER NOT NULL,
    proyectos_count     INTEGER NOT NULL DEFAULT 0,
    monto_corfo         NUMERIC NOT NULL DEFAULT 0,  -- SUM(aprobado_corfo)
    monto_privado       NUMERIC NOT NULL DEFAULT 0,  -- SUM(aprobado_privado)
    monto_ley           NUMERIC NOT NULL DEFAULT 0,  -- SUM(monto_consolidado_ley)
    sectores            TEXT,                        -- valores únicos separados por coma
    instrumentos        TEXT,                        -- instrumento_homologado únicos
    PRIMARY KEY (rut_beneficiario, "año_adjudicacion")
);

-- ── leads ─────────────────────────────────────────────────────────────────────
-- CRM pipeline por usuario. Solo admin puede escribir; viewer puede leer.
CREATE TABLE IF NOT EXISTS leads (
    id              SERIAL      PRIMARY KEY,
    user_id         TEXT        NOT NULL,
    nombre_compania TEXT        NOT NULL,
    contacto        TEXT,
    status          TEXT        NOT NULL DEFAULT 'Nuevo'
                    CHECK (status IN (
                        'Nuevo',
                        'Contactado',
                        'En seguimiento',
                        'Propuesta enviada',
                        'Cerrado'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── _sync_log ─────────────────────────────────────────────────────────────────
-- Registro de cada ejecución del sync mensual.
CREATE TABLE IF NOT EXISTS _sync_log (
    id            SERIAL      PRIMARY KEY,
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    rows_fetched  INTEGER,
    rows_upserted INTEGER,
    status        TEXT,
    error_message TEXT,
    source        TEXT,
    rows_inserted INTEGER,
    rows_updated  INTEGER,
    rows_skipped  INTEGER
);

-- ── proyectos_vec ────────────────────────────────────────────────────────────
-- Embedding vectors for semantic search. Populated by build_embeddings.py.
-- Vector stored as BYTEA (float32 array serialized with numpy .tobytes()).
CREATE TABLE IF NOT EXISTS proyectos_vec (
    codigo  TEXT PRIMARY KEY REFERENCES proyectos(codigo) ON DELETE CASCADE,
    vector  BYTEA NOT NULL
);

-- ── sector_canonico ───────────────────────────────────────────────────────────
-- Normalización de sector_economico: mapea variantes ortográficas al valor
-- canónico que ve el usuario. Poblada por sync/sector_normalizacion.py.
CREATE TABLE IF NOT EXISTS sector_canonico (
    sector_raw     TEXT PRIMARY KEY,
    sector_display TEXT NOT NULL
);

-- ── Índices ───────────────────────────────────────────────────────────────────

-- proyectos: columnas de filtro más frecuentes en queries NL→SQL
CREATE INDEX IF NOT EXISTS idx_proyectos_razon
    ON proyectos (razon);

CREATE INDEX IF NOT EXISTS idx_proyectos_anio
    ON proyectos ("año_adjudicacion");

CREATE INDEX IF NOT EXISTS idx_proyectos_region
    ON proyectos (region_ejecucion);

CREATE INDEX IF NOT EXISTS idx_proyectos_sector
    ON proyectos (sector_economico);

CREATE INDEX IF NOT EXISTS idx_proyectos_rut
    ON proyectos (rut_beneficiario);

-- empresas: JOINs desde leads y adjudicaciones, columnas de filtro
CREATE INDEX IF NOT EXISTS idx_empresas_sector
    ON empresas (sector_economico);

CREATE INDEX IF NOT EXISTS idx_empresas_region
    ON empresas (region_ejecucion_principal);

CREATE INDEX IF NOT EXISTS idx_empresas_tramo
    ON empresas (tramo_ventas);

-- adjudicaciones: búsquedas temporales y por empresa
CREATE INDEX IF NOT EXISTS idx_adj_rut
    ON adjudicaciones (rut_beneficiario);

CREATE INDEX IF NOT EXISTS idx_adj_anio
    ON adjudicaciones ("año_adjudicacion");

-- leads: filtro por usuario (cada usuario ve solo sus leads)
CREATE INDEX IF NOT EXISTS idx_leads_user_id
    ON leads (user_id);

-- users: login lookup
CREATE INDEX IF NOT EXISTS idx_users_org_username
    ON users (org_id, username);
