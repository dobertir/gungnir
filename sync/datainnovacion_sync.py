"""
sync/datainnovacion_sync.py
----------------------------
Monthly sync job: pulls proyectos from datainnovacion.cl/api and upserts into
the database (PostgreSQL on Railway, SQLite locally).
Never touches the leads table.

Run manually:   python sync/datainnovacion_sync.py
Run from Flask: POST /api/sync  (calls run_sync() directly)
Scheduled:      APScheduler calls run_sync() once a month (configured in corfo_server.py)
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

from sync.entity_resolution import resolve_entities
from sync.quality_checks import validate_proyectos
from sync.sector_normalizacion import ensure_sector_canonico_table, rebuild_sector_canonico

load_dotenv()

log = logging.getLogger("corfo.sync")

# ── Database driver selection ─────────────────────────────────────────────────
# PostgreSQL (psycopg2) when DATABASE_URL is set; SQLite otherwise (local dev).

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False

def _resolve_database_url() -> str | None:
    # PG* individual vars take priority — Railway injects these reliably per-service.
    pguser = os.environ.get("PGUSER", "").strip()
    pghost = os.environ.get("PGHOST", "").strip()
    pgdatabase = os.environ.get("PGDATABASE", "").strip()
    if pguser and pghost and pgdatabase:
        pgpassword = os.environ.get("PGPASSWORD", "").strip()
        pgport = os.environ.get("PGPORT", "5432").strip()
        return f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    # Fall back to pre-built URL vars (local dev / `railway run`)
    return (
        os.environ.get("DATABASE_PUBLIC_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
        or None
    )

_DATABASE_URL = _resolve_database_url()

# ── Config ────────────────────────────────────────────────────────────────────

API_URL   = "https://datainnovacion.cl/api/v1/proyectos"
DB_PATH   = os.getenv("DB_PATH", "corfo_alimentos.db")


def _get_headers() -> dict:
    token = os.getenv("DATAINNOVACION_TOKEN")
    if not token:
        raise RuntimeError("DATAINNOVACION_TOKEN env var no está configurada")
    return {"Accept": "application/json", "Authorization": token}


def is_postgres() -> bool:
    return bool(_DATABASE_URL and _PSYCOPG2_AVAILABLE)


def get_db():
    """Return a database connection (PostgreSQL or SQLite based on environment)."""
    if is_postgres():
        # Re-resolve at connection time so Railway's runtime injection is captured.
        url = _resolve_database_url() or _DATABASE_URL
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url)
    import sqlite3
    return sqlite3.connect(DB_PATH)


def get_cursor(conn):
    """Return a cursor (RealDictCursor for PG, standard cursor for SQLite)."""
    if is_postgres():
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()


def _sql(query: str) -> str:
    """Translate ? placeholders to %s for PostgreSQL."""
    if is_postgres():
        return query.replace("?", "%s")
    return query


# ── Column mapping: API field → DB column ─────────────────────────────────────
# These are the REAL column names from the proyectos table (37 columns).
# The API likely returns the same names since the DB was built by pd.json_normalize().
# If the API field name differs, adjust the key (left side). The value (right side)
# must match the DB column name exactly.
#
# To verify API field names, run once manually:
#   import requests, pandas as pd
#   r = requests.get(API_URL, headers=HEADERS)
#   df = pd.json_normalize(r.json())
#   print(df.columns.tolist())

COLUMN_MAP = {
    # API field name                  : DB column name
    #
    # As of 2026-04, the API returns field names that match DB column names directly.
    # All mappings are therefore identity except where noted.
    "codigo"                          : "codigo",
    "foco_apoyo"                      : "foco_apoyo",
    "tipo_intervencion"               : "tipo_intervencion",
    "instrumento"                     : "instrumento",
    "instrumento_homologado"          : "instrumento_homologado",
    "estado_data"                     : "estado_data",
    "tipo_persona_beneficiario"       : "tipo_persona_beneficiario",
    "rut_beneficiario"                : "rut_beneficiario",
    "razon"                           : "razon",
    "titulo_del_proyecto"             : "titulo_del_proyecto",
    "objetivo_general_del_proyecto"   : "objetivo_general_del_proyecto",
    "año_adjudicacion"                : "año_adjudicacion",
    "aprobado_corfo"                  : "aprobado_corfo",
    "aprobado_privado"                : "aprobado_privado",
    "aprobado_privado_pecuniario"     : "aprobado_privado_pecuniario",
    "monto_consolidado_ley"           : "monto_consolidado_ley",
    "tipo_innovacion"                 : "tipo_innovacion",
    "mercado_objetivo_final"          : "mercado_objetivo_final",
    "criterio_mujer"                  : "criterio_mujer",
    "genero_director"                 : "genero_director",
    "sostenible"                      : "sostenible",
    "ods_principal_sostenible"        : "ods_principal_sostenible",
    "meta_principal_cod"              : "meta_principal_cod",
    "economia_circular_si_no"         : "economia_circular_si_no",
    "modelo_de_circularidad"          : "modelo_de_circularidad",
    "region_ejecucion"                : "region_ejecucion",
    "tramo_ventas"                    : "tramo_ventas",
    "inicio_actividad"                : "inicio_actividad",
    "sector_economico"                : "sector_economico",
    "patron_principal_asociado"       : "patron_principal_asociado",
    "tipo_proyecto"                   : "tipo_proyecto",
    "r_principal"                     : "r_principal",
    "estrategia_r_principal"          : "estrategia_r_principal",
    "ley_rep_si_no"                   : "ley_rep_si_no",
    "ley_rep"                         : "ley_rep",
    "ernc"                            : "ernc",
    "tendencia_final"                 : "tendencia_final",
}

# Primary key for upsert deduplication.
# 'codigo' is unique across all rows — confirmed from DB inspection.
# The API returns this field as "id"; after COLUMN_MAP rename it becomes "codigo" in the DB.
PRIMARY_KEY_API   = "codigo"   # API field name (same as DB column name)
PRIMARY_KEY_DB    = "codigo"   # DB column name


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_proyectos() -> pd.DataFrame:
    """Pull all proyectos from the API. Returns a normalized DataFrame."""
    log.info("Fetching proyectos from %s", API_URL)
    try:
        r = requests.get(API_URL, headers=_get_headers(), timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"API request failed: {e}") from e

    raw = r.json()

    if not raw:
        raise RuntimeError("API returned an empty response")

    df = pd.json_normalize(raw)
    log.info("Fetched %d records from API", len(df))
    return df


# ── Transform ─────────────────────────────────────────────────────────────────

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename API columns to canonical DB column names, coerce types, and validate rows.

    Steps:
      1. Select only columns present in COLUMN_MAP (drop unmapped extras silently).
      2. Rename API field names → DB column names via COLUMN_MAP.
      3. Drop rows where the primary key (codigo) is null or empty — log count.
      4. Coerce año_adjudicacion to INTEGER; drop rows where coercion fails.
      5. Keep aprobado_corfo as object dtype for SQLite TEXT compatibility.
         In PostgreSQL the column is NUMERIC — the value is cast at insert time.
      6. Log summary: rows received, rows dropped, rows output.
    """
    rows_received = len(df)

    # Keep only columns we have a mapping for (COLUMN_MAP keys = API field names)
    available = [c for c in COLUMN_MAP.keys() if c in df.columns]
    missing   = [c for c in COLUMN_MAP.keys() if c not in df.columns]
    if missing:
        log.warning("API columns not found in response (check COLUMN_MAP): %s", missing)

    df = df[available].copy()

    # Rename API field names → DB column names
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Drop rows where primary key is missing — these cannot be upserted
    if PRIMARY_KEY_DB in df.columns:
        before_pk_drop = len(df)
        df = df[df[PRIMARY_KEY_DB].notna() & (df[PRIMARY_KEY_DB].astype(str).str.strip() != "")]
        dropped_pk = before_pk_drop - len(df)
        if dropped_pk > 0:
            log.warning("Dropped %d rows with missing primary key ('%s')", dropped_pk, PRIMARY_KEY_DB)

    # año_adjudicacion must be INTEGER — drop rows where coercion fails
    if "año_adjudicacion" in df.columns:
        df["año_adjudicacion"] = pd.to_numeric(df["año_adjudicacion"], errors="coerce").astype("Int64")
        bad_year_mask = df["año_adjudicacion"].isna()
        if bad_year_mask.any():
            log.warning(
                "Dropped %d rows with non-integer 'año_adjudicacion' value", int(bad_year_mask.sum())
            )
            df = df[~bad_year_mask]

    # aprobado_corfo: keep as object dtype to match SQLite TEXT; psycopg2 will
    # coerce to NUMERIC automatically when inserting into a NUMERIC column.
    if "aprobado_corfo" in df.columns:
        df["aprobado_corfo"] = df["aprobado_corfo"].astype(object)

    rows_output  = len(df)
    rows_dropped = rows_received - rows_output
    log.info(
        "Transform summary — received: %d, dropped: %d, output: %d",
        rows_received, rows_dropped, rows_output,
    )

    return df


# ── Ensure schema ─────────────────────────────────────────────────────────────

def ensure_sync_log_table(conn) -> None:
    """
    Create _sync_log table if it doesn't exist, then migrate missing columns.
    No-op in PostgreSQL — schema is managed by 003_create_postgresql_schema.sql.
    """
    if is_postgres():
        log.debug("ensure_sync_log_table: omitido en modo PostgreSQL")
        return

    import sqlite3
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _sync_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at      TEXT NOT NULL,
            finished_at     TEXT,
            source          TEXT NOT NULL,
            rows_fetched    INTEGER,
            status          TEXT NOT NULL,
            rows_upserted   INTEGER,
            error_message   TEXT
        )
    """)
    conn.commit()
    # Migrate: add missing columns if table already existed with old schema
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(_sync_log)")}
    for col_name, col_type in [
        ("source", "TEXT"),
        ("rows_upserted", "INTEGER"),
        ("quality_summary", "TEXT"),
    ]:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE _sync_log ADD COLUMN {col_name} {col_type}")
    conn.commit()


def ensure_match_confidence_column(conn) -> None:
    """
    Add match_confidence column to empresas if it does not already exist.
    No-op in PostgreSQL — column is defined in 003_create_postgresql_schema.sql.
    """
    if is_postgres():
        return

    import sqlite3
    try:
        conn.execute("ALTER TABLE empresas ADD COLUMN match_confidence REAL DEFAULT 1.0")
        conn.commit()
        log.info("Added match_confidence column to empresas")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            pass  # Already exists — nothing to do
        elif "no such table" in str(e):
            log.warning("ensure_match_confidence_column: empresas table does not exist yet, skipping")
        else:
            raise


def ensure_quality_summary_column(conn) -> None:
    """
    Add quality_summary TEXT column to _sync_log if it does not already exist.

    SQLite: uses ALTER TABLE (idempotent via try/except).
    PostgreSQL: uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS (idempotent natively).
    """
    if is_postgres():
        try:
            cur = get_cursor(conn)
            cur.execute(
                "ALTER TABLE _sync_log ADD COLUMN IF NOT EXISTS quality_summary TEXT"
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.warning("ensure_quality_summary_column (PG): %s", e)
        return

    import sqlite3
    try:
        conn.execute("ALTER TABLE _sync_log ADD COLUMN quality_summary TEXT")
        conn.commit()
        log.info("Added quality_summary column to _sync_log")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            pass  # Already exists — nothing to do
        else:
            raise


def ensure_proyectos_pk_column(conn) -> None:
    """
    Verify that the primary key column exists in proyectos.
    No-op in PostgreSQL — column is defined in 003_create_postgresql_schema.sql.
    """
    if is_postgres():
        return

    cur = conn.execute("PRAGMA table_info(proyectos)")
    cols = [row[1] for row in cur.fetchall()]
    if PRIMARY_KEY_DB not in cols:
        log.info("Adding column '%s' to proyectos table", PRIMARY_KEY_DB)
        conn.execute(f"ALTER TABLE proyectos ADD COLUMN \"{PRIMARY_KEY_DB}\" TEXT")
        conn.commit()
    else:
        log.debug("Primary key column '%s' already exists — OK", PRIMARY_KEY_DB)


# ── Upsert ────────────────────────────────────────────────────────────────────

def upsert_proyectos(conn, df: pd.DataFrame) -> int:
    """
    Upsert rows into proyectos. Returns the total number of rows processed.

    PostgreSQL: single INSERT ... ON CONFLICT DO UPDATE per row (atomic, fast).
    SQLite: INSERT OR IGNORE + conditional UPDATE (preserves insert/update/skip tracking).
    """
    if df.empty:
        log.warning("Nothing to upsert — dataframe is empty")
        return 0

    cols      = df.columns.tolist()
    col_names = ", ".join([f'"{c}"' for c in cols])
    non_pk_cols = [c for c in cols if c != PRIMARY_KEY_DB]

    if is_postgres():
        from psycopg2.extras import execute_values
        import numpy as np

        upsert_sql = (
            f'INSERT INTO proyectos ({col_names}) VALUES %s '
            f'ON CONFLICT ("{PRIMARY_KEY_DB}") DO UPDATE SET '
            + ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in non_pk_cols)
        )

        def _native(v):
            if isinstance(v, np.integer):
                return int(v)
            if isinstance(v, np.floating):
                return None if np.isnan(v) else float(v)
            if isinstance(v, float) and np.isnan(v):
                return None
            return v

        rows = [[_native(v) for v in row] for row in df.itertuples(index=False, name=None)]
        cur = get_cursor(conn)
        BATCH = 200
        for i in range(0, len(rows), BATCH):
            execute_values(cur, upsert_sql, rows[i:i + BATCH], page_size=BATCH)
            conn.commit()
            log.info("Upsert PostgreSQL: %d/%d filas procesadas", min(i + BATCH, len(rows)), len(rows))
        total = len(df)
        log.info("Upsert complete (PostgreSQL) — %d rows processed", total)
        return total

    # SQLite path: INSERT OR IGNORE + selective UPDATE
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f'INSERT OR IGNORE INTO proyectos ({col_names}) VALUES ({placeholders})'
    update_sql = (
        f'UPDATE proyectos SET '
        + ", ".join(f'"{c}"=?' for c in non_pk_cols)
        + f' WHERE "{PRIMARY_KEY_DB}"=?'
    )

    # Pre-fetch existing PKs for skip detection
    existing_pks: set = set()
    cur = conn.execute(f'SELECT "{PRIMARY_KEY_DB}" FROM proyectos')
    for r in cur.fetchall():
        existing_pks.add(r[0])

    inserted = 0
    updated  = 0
    skipped  = 0
    pk_idx   = cols.index(PRIMARY_KEY_DB)

    for row in df.itertuples(index=False, name=None):
        row_list = list(row)
        pk_val   = row_list[pk_idx]

        if pk_val not in existing_pks:
            conn.execute(insert_sql, row_list)
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                inserted += 1
                existing_pks.add(pk_val)
        else:
            quoted_non_pk = ", ".join(f'"{c}"' for c in non_pk_cols)
            db_row = conn.execute(
                f'SELECT {quoted_non_pk} FROM proyectos WHERE "{PRIMARY_KEY_DB}"=?',
                (pk_val,)
            ).fetchone()
            new_non_pk = [row_list[cols.index(c)] for c in non_pk_cols]
            if db_row is not None and list(db_row) == new_non_pk:
                skipped += 1
            else:
                conn.execute(update_sql, new_non_pk + [pk_val])
                updated += 1

    conn.commit()
    log.info(
        "Upsert complete (SQLite) — inserted: %d, updated: %d, skipped: %d",
        inserted, updated, skipped,
    )
    return inserted + updated


# ── Rebuild derived tables ────────────────────────────────────────────────────

def rebuild_empresas(conn) -> int:
    """
    Rebuild empresas from proyectos using entity resolution to group companies.

    Steps:
      1. Load all proyectos into a DataFrame.
      2. Run resolve_entities() to assign canonical_rut and match_confidence.
      3. For each canonical_rut group, aggregate into one empresas row.
      4. Upsert via INSERT ... ON CONFLICT DO UPDATE so that created_at is
         preserved on re-sync.

    Returns the number of rows inserted or updated.
    """
    df = pd.read_sql_query(
        """SELECT rut_beneficiario, razon, sector_economico, region_ejecucion,
                  tramo_ventas, inicio_actividad, aprobado_corfo,
                  "año_adjudicacion", tipo_persona_beneficiario, aprobado_privado,
                  monto_consolidado_ley
           FROM proyectos""",
        conn,
    )

    if df.empty:
        log.warning("rebuild_empresas: proyectos table is empty — nothing to rebuild")
        return 0

    df = resolve_entities(df, rut_col="rut_beneficiario", name_col="razon")

    df["aprobado_corfo_num"] = pd.to_numeric(df["aprobado_corfo"], errors="coerce").fillna(0.0)
    df["año_adjudicacion"] = pd.to_numeric(df["año_adjudicacion"], errors="coerce")

    updated_at = datetime.utcnow().isoformat()
    empresa_rows = []
    for canonical_rut, group in df.groupby("canonical_rut", sort=False):
        latest = group.sort_values("año_adjudicacion", ascending=False).iloc[0]
        region_counts = group["region_ejecucion"].value_counts()
        empresa_rows.append((
            canonical_rut,
            latest["razon"],
            latest["sector_economico"],
            region_counts.index[0] if not region_counts.empty else None,
            latest["tramo_ventas"],
            latest["inicio_actividad"],
            len(group),
            float(group["aprobado_corfo_num"].sum()),
            int(group["año_adjudicacion"].min()) if group["año_adjudicacion"].notna().any() else None,
            int(group["año_adjudicacion"].max()) if group["año_adjudicacion"].notna().any() else None,
            latest["tipo_persona_beneficiario"],
            float(group["match_confidence"].min()),
            updated_at,
        ))

    cur = get_cursor(conn)
    if is_postgres():
        from psycopg2.extras import execute_values
        upsert_sql = """
            INSERT INTO empresas (
                rut_beneficiario, razon_social_canonical, sector_economico,
                region_ejecucion_principal, tramo_ventas, inicio_actividad,
                total_proyectos, monto_total_aprobado_corfo,
                primera_adjudicacion, ultima_adjudicacion,
                tipo_persona_beneficiario, match_confidence, updated_at
            ) VALUES %s
            ON CONFLICT (rut_beneficiario) DO UPDATE SET
                razon_social_canonical     = EXCLUDED.razon_social_canonical,
                sector_economico           = EXCLUDED.sector_economico,
                region_ejecucion_principal = EXCLUDED.region_ejecucion_principal,
                tramo_ventas               = EXCLUDED.tramo_ventas,
                inicio_actividad           = EXCLUDED.inicio_actividad,
                total_proyectos            = EXCLUDED.total_proyectos,
                monto_total_aprobado_corfo = EXCLUDED.monto_total_aprobado_corfo,
                primera_adjudicacion       = EXCLUDED.primera_adjudicacion,
                ultima_adjudicacion        = EXCLUDED.ultima_adjudicacion,
                tipo_persona_beneficiario  = EXCLUDED.tipo_persona_beneficiario,
                match_confidence           = EXCLUDED.match_confidence,
                updated_at                 = EXCLUDED.updated_at
        """
        BATCH = 200
        for i in range(0, len(empresa_rows), BATCH):
            execute_values(cur, upsert_sql, empresa_rows[i:i + BATCH], page_size=BATCH)
            conn.commit()
        total = len(empresa_rows)
    else:
        rows_inserted = rows_updated = 0
        for row in empresa_rows:
            cur.execute(_sql("SELECT 1 FROM empresas WHERE rut_beneficiario = ?"), (row[0],))
            if cur.fetchone() is None:
                cur.execute(_sql("""INSERT INTO empresas (
                    rut_beneficiario, razon_social_canonical, sector_economico,
                    region_ejecucion_principal, tramo_ventas, inicio_actividad,
                    total_proyectos, monto_total_aprobado_corfo,
                    primera_adjudicacion, ultima_adjudicacion,
                    tipo_persona_beneficiario, match_confidence, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""), row)
                rows_inserted += 1
            else:
                cur.execute(_sql("""UPDATE empresas SET
                    razon_social_canonical=?, sector_economico=?, region_ejecucion_principal=?,
                    tramo_ventas=?, inicio_actividad=?, total_proyectos=?,
                    monto_total_aprobado_corfo=?, primera_adjudicacion=?, ultima_adjudicacion=?,
                    tipo_persona_beneficiario=?, match_confidence=?, updated_at=?
                    WHERE rut_beneficiario=?"""), row[1:] + (row[0],))
                rows_updated += 1
        conn.commit()
        total = rows_inserted + rows_updated

    log.info("rebuild_empresas complete — %d empresas procesadas", total)
    return total


def rebuild_adjudicaciones(conn) -> int:
    """
    Rebuild adjudicaciones from proyectos using INSERT ... ON CONFLICT DO UPDATE.
    Returns row count processed.

    PostgreSQL: STRING_AGG(DISTINCT ..., ',') instead of GROUP_CONCAT(DISTINCT ...).
    SQLite: GROUP_CONCAT(DISTINCT ...) and CAST to REAL for money columns.
    """
    if is_postgres():
        sql = """
            INSERT INTO adjudicaciones (
                rut_beneficiario,
                "año_adjudicacion",
                proyectos_count,
                monto_corfo,
                monto_privado,
                monto_ley,
                sectores,
                instrumentos
            )
            SELECT
                rut_beneficiario,
                "año_adjudicacion",
                COUNT(*) AS proyectos_count,
                SUM(aprobado_corfo) AS monto_corfo,
                SUM(aprobado_privado) AS monto_privado,
                SUM(monto_consolidado_ley) AS monto_ley,
                STRING_AGG(DISTINCT sector_economico, ',') AS sectores,
                STRING_AGG(DISTINCT instrumento_homologado, ',') AS instrumentos
            FROM proyectos
            WHERE rut_beneficiario IS NOT NULL
              AND rut_beneficiario != ''
            GROUP BY rut_beneficiario, "año_adjudicacion"
            ON CONFLICT(rut_beneficiario, "año_adjudicacion") DO UPDATE SET
                proyectos_count = EXCLUDED.proyectos_count,
                monto_corfo     = EXCLUDED.monto_corfo,
                monto_privado   = EXCLUDED.monto_privado,
                monto_ley       = EXCLUDED.monto_ley,
                sectores        = EXCLUDED.sectores,
                instrumentos    = EXCLUDED.instrumentos
        """
        cur = get_cursor(conn)
        cur.execute(sql)
        conn.commit()
        count = cur.rowcount
    else:
        sql = """
            INSERT INTO adjudicaciones (
                rut_beneficiario,
                "año_adjudicacion",
                proyectos_count,
                monto_corfo,
                monto_privado,
                monto_ley,
                sectores,
                instrumentos
            )
            SELECT
                rut_beneficiario,
                "año_adjudicacion",
                COUNT(*) AS proyectos_count,
                SUM(CAST(aprobado_corfo AS REAL)) AS monto_corfo,
                SUM(CAST(aprobado_privado AS REAL)) AS monto_privado,
                SUM(CAST(monto_consolidado_ley AS REAL)) AS monto_ley,
                GROUP_CONCAT(DISTINCT sector_economico) AS sectores,
                GROUP_CONCAT(DISTINCT instrumento_homologado) AS instrumentos
            FROM proyectos
            WHERE rut_beneficiario IS NOT NULL
              AND rut_beneficiario != ''
            GROUP BY rut_beneficiario, "año_adjudicacion"
            ON CONFLICT(rut_beneficiario, "año_adjudicacion") DO UPDATE SET
                proyectos_count = excluded.proyectos_count,
                monto_corfo     = excluded.monto_corfo,
                monto_privado   = excluded.monto_privado,
                monto_ley       = excluded.monto_ley,
                sectores        = excluded.sectores,
                instrumentos    = excluded.instrumentos
        """
        conn.execute(sql)
        conn.commit()
        count = conn.execute("SELECT changes()").fetchone()[0]

    log.info("rebuild_adjudicaciones complete — %d rows processed", count)
    return count


# ── Main sync ─────────────────────────────────────────────────────────────────

def run_sync() -> dict:
    """
    Full sync cycle. Returns a summary dict with log row data.
    Safe to call from Flask route or scheduler.

    IMPORTANT: This function NEVER touches the leads table.
    """
    started_at = datetime.utcnow().isoformat()
    log.info("=== Sync iniciado en %s ===", started_at)

    conn = get_db()
    log_id = None
    try:
        ensure_sync_log_table(conn)
        ensure_quality_summary_column(conn)

        cur = get_cursor(conn)
        if is_postgres():
            cur.execute(
                "INSERT INTO _sync_log (started_at, source, status) VALUES (%s, %s, 'running') RETURNING id",
                (started_at, "datainnovacion.cl/api"),
            )
            row = cur.fetchone()
            conn.commit()
            log_id = row["id"] if isinstance(row, dict) else row[0]
        else:
            cur.execute(
                "INSERT INTO _sync_log (started_at, source, status) VALUES (?, ?, 'running')",
                (started_at, "datainnovacion.cl/api"),
            )
            conn.commit()
            log_id = cur.lastrowid

        rows_fetched  = 0
        rows_upserted = 0

        df = fetch_proyectos()
        rows_fetched = len(df)

        df = transform(df)

        ensure_proyectos_pk_column(conn)
        rows_upserted = upsert_proyectos(conn, df)

        ensure_match_confidence_column(conn)

        try:
            n_empresas = rebuild_empresas(conn)
            log.info("empresas reconstruidas: %d filas insertadas/actualizadas", n_empresas)
        except Exception as e:
            log.warning("Rebuild de empresas falló (no crítico): %s", e)

        try:
            n_adj = rebuild_adjudicaciones(conn)
            log.info("adjudicaciones reconstruidas: %d filas insertadas/actualizadas", n_adj)
        except Exception as e:
            log.warning("Rebuild de adjudicaciones falló (no crítico): %s", e)

        try:
            ensure_sector_canonico_table(conn)
            n_sec = rebuild_sector_canonico(conn)
            log.info("sector_canonico reconstruida: %d mapeos cargados", n_sec)
        except Exception as e:
            log.warning("Rebuild de sector_canonico falló (no crítico): %s", e)

        quality_result = validate_proyectos(conn)
        log.info(
            "Quality check: passed=%s, checks=%s",
            quality_result["passed"],
            quality_result["checks"],
        )

        finished_at = datetime.utcnow().isoformat()
        quality_json = json.dumps(quality_result, ensure_ascii=False)
        cur2 = get_cursor(conn)
        cur2.execute(
            _sql("""UPDATE _sync_log
               SET finished_at=?, rows_fetched=?, rows_upserted=?, status='ok',
                   quality_summary=?
               WHERE id=?"""),
            (finished_at, rows_fetched, rows_upserted, quality_json, log_id),
        )
        conn.commit()
        log.info(
            "=== Sync completado: %d obtenidos, %d actualizados/insertados ===",
            rows_fetched, rows_upserted,
        )

        # Embeddings are re-indexed by corfo_server._trigger_embeddings_rebuild()
        # after a successful sync call via /api/sync. The sync module does not
        # call build_embeddings.py directly to avoid subprocess OOM on Railway.

        return {
            "id": log_id,
            "status": "ok",
            "source": API_URL,
            "started_at": started_at,
            "finished_at": finished_at,
            "rows_fetched": rows_fetched,
            "rows_upserted": rows_upserted,
            "error_message": None,
        }

    except Exception as e:
        log.error("Sync falló: %s", e)
        if log_id is not None:
            try:
                cur_err = get_cursor(conn)
                cur_err.execute(
                    _sql("UPDATE _sync_log SET status='error', finished_at=?, error_message=? WHERE id=?"),
                    (datetime.utcnow().isoformat(), str(e), log_id),
                )
                conn.commit()
            except Exception as update_err:
                log.error("No se pudo registrar error en _sync_log: %s", update_err)
        return {"status": "error", "error_message": str(e), "rows_fetched": 0,
                "rows_upserted": 0}
    finally:
        conn.close()


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    )
    result = run_sync()
    print("\nSync result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
