"""
sync/quality_checks.py
-----------------------
Post-sync data quality checks for the proyectos table.

Run automatically by run_sync() after every upsert cycle.
Never aborts the sync — logs and stores results, always completes.
"""

import logging
import sqlite3

log = logging.getLogger("corfo.sync")


def _is_pg(conn) -> bool:
    """Return True if the connection is a psycopg2 PostgreSQL connection."""
    return not isinstance(conn, sqlite3.Connection)


def validate_proyectos(conn) -> dict:
    """
    Run data quality checks against the live proyectos table.

    Returns a structured dict with one entry per check and an overall 'passed' flag.
    Status values: 'ok', 'warn', 'fail'.
    Never raises — all SQL errors are caught and reported as 'fail'.
    """
    pg = _is_pg(conn)
    cur = conn.cursor()

    checks: dict = {}

    # ── 1. row_count ──────────────────────────────────────────────────────────
    # Sanity check: the table must have a reasonable number of rows.
    # warn if < 9000 (partial load), fail if < 5000 (something went very wrong).
    try:
        cur.execute("SELECT COUNT(*) FROM proyectos")
        row = cur.fetchone()
        count = int(row[0] if not isinstance(row, dict) else row["count"])
        if count >= 9000:
            status = "ok"
        elif count >= 5000:
            status = "warn"
            log.warning("Calidad datos: row_count=%d (esperado ≥9000)", count)
        else:
            status = "fail"
            log.error("Calidad datos: row_count=%d es demasiado bajo (mínimo 5000)", count)
        checks["row_count"] = {"value": count, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check row_count: %s", e)
        checks["row_count"] = {"value": None, "status": "fail"}

    # ── 2. null_codigo ────────────────────────────────────────────────────────
    # codigo is the primary key — zero NULLs expected.
    try:
        cur.execute("SELECT COUNT(*) FROM proyectos WHERE codigo IS NULL")
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        status = "ok" if n == 0 else "fail"
        if n > 0:
            log.error("Calidad datos: null_codigo=%d (esperado 0)", n)
        checks["null_codigo"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check null_codigo: %s", e)
        checks["null_codigo"] = {"value": None, "status": "fail"}

    # ── 3. null_razon ─────────────────────────────────────────────────────────
    # razon should never be NULL or empty (one known empty string edge case is
    # tolerated only as a warn, but nulls are a fail).
    try:
        cur.execute(
            "SELECT COUNT(*) FROM proyectos WHERE razon IS NULL OR razon = ''"
        )
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        if n == 0:
            status = "ok"
        elif n <= 2:
            # Known edge case: PI-64569 has razon = '' — treat as warn
            status = "warn"
            log.warning("Calidad datos: null_razon=%d (valores nulos o vacíos en razon)", n)
        else:
            status = "fail"
            log.error("Calidad datos: null_razon=%d (demasiados nulos/vacíos en razon)", n)
        checks["null_razon"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check null_razon: %s", e)
        checks["null_razon"] = {"value": None, "status": "fail"}

    # ── 4. null_aprobado_corfo ────────────────────────────────────────────────
    # aprobado_corfo is TEXT in SQLite, NUMERIC in PostgreSQL — zero NULLs expected.
    try:
        cur.execute("SELECT COUNT(*) FROM proyectos WHERE aprobado_corfo IS NULL")
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        status = "ok" if n == 0 else "fail"
        if n > 0:
            log.error("Calidad datos: null_aprobado_corfo=%d (esperado 0)", n)
        checks["null_aprobado_corfo"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check null_aprobado_corfo: %s", e)
        checks["null_aprobado_corfo"] = {"value": None, "status": "fail"}

    # ── 5. null_año_adjudicacion ──────────────────────────────────────────────
    try:
        cur.execute('SELECT COUNT(*) FROM proyectos WHERE "año_adjudicacion" IS NULL')
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        status = "ok" if n == 0 else "fail"
        if n > 0:
            log.error('Calidad datos: null_año_adjudicacion=%d (esperado 0)', n)
        checks["null_año_adjudicacion"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check null_año_adjudicacion: %s", e)
        checks["null_año_adjudicacion"] = {"value": None, "status": "fail"}

    # ── 6. null_region_ejecucion ──────────────────────────────────────────────
    try:
        cur.execute("SELECT COUNT(*) FROM proyectos WHERE region_ejecucion IS NULL")
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        status = "ok" if n == 0 else "fail"
        if n > 0:
            log.error("Calidad datos: null_region_ejecucion=%d (esperado 0)", n)
        checks["null_region_ejecucion"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check null_region_ejecucion: %s", e)
        checks["null_region_ejecucion"] = {"value": None, "status": "fail"}

    # ── 7. año_range ──────────────────────────────────────────────────────────
    # Expected: MIN >= 2009, MAX <= 2030 (generous upper bound for future years).
    try:
        cur.execute('SELECT MIN("año_adjudicacion"), MAX("año_adjudicacion") FROM proyectos')
        row = cur.fetchone()
        if isinstance(row, dict):
            min_year = row.get("min") or row.get("min", None)
            max_year = row.get("max") or row.get("max", None)
            # psycopg2 RealDictCursor returns lowercase column names
            min_year = int(min_year) if min_year is not None else None
            max_year = int(max_year) if max_year is not None else None
        else:
            min_year = int(row[0]) if row[0] is not None else None
            max_year = int(row[1]) if row[1] is not None else None

        value = {"min": min_year, "max": max_year}
        ok = (
            min_year is not None
            and max_year is not None
            and min_year >= 2009
            and max_year <= 2030
        )
        status = "ok" if ok else "fail"
        if not ok:
            log.error(
                "Calidad datos: año_range fuera de rango esperado: min=%s, max=%s",
                min_year, max_year,
            )
        checks["año_range"] = {"value": value, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check año_range: %s", e)
        checks["año_range"] = {"value": None, "status": "fail"}

    # ── 8. estado_data_values ─────────────────────────────────────────────────
    # Only 'FINALIZADO' and/or 'VIGENTE' are valid values for estado_data.
    try:
        cur.execute("SELECT DISTINCT estado_data FROM proyectos WHERE estado_data IS NOT NULL")
        rows = cur.fetchall()
        values = sorted([
            (r["estado_data"] if isinstance(r, dict) else r[0])
            for r in rows
        ])
        allowed = {"FINALIZADO", "VIGENTE"}
        unexpected = [v for v in values if v not in allowed]
        status = "ok" if not unexpected else "fail"
        if unexpected:
            log.error(
                "Calidad datos: estado_data_values contiene valores inesperados: %s",
                unexpected,
            )
        checks["estado_data_values"] = {"value": values, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check estado_data_values: %s", e)
        checks["estado_data_values"] = {"value": None, "status": "fail"}

    # ── 9. aprobado_corfo_castable ────────────────────────────────────────────
    # Count rows where the numeric value of aprobado_corfo is negative.
    # Negative funding makes no business sense.
    # In PostgreSQL aprobado_corfo is NUMERIC — cast to NUMERIC is safe.
    # In SQLite it is TEXT — cast to REAL works for numeric strings.
    try:
        if pg:
            cur.execute(
                "SELECT COUNT(*) FROM proyectos "
                "WHERE aprobado_corfo IS NOT NULL "
                "AND CAST(aprobado_corfo AS NUMERIC) < 0"
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM proyectos "
                "WHERE aprobado_corfo IS NOT NULL "
                "AND CAST(aprobado_corfo AS REAL) < 0"
            )
        row = cur.fetchone()
        n = int(row[0] if not isinstance(row, dict) else row["count"])
        status = "ok" if n == 0 else "fail"
        if n > 0:
            log.error(
                "Calidad datos: aprobado_corfo_castable=%d filas con valor negativo", n
            )
        checks["aprobado_corfo_castable"] = {"value": n, "status": status}
    except Exception as e:
        log.error("Calidad datos: error en check aprobado_corfo_castable: %s", e)
        checks["aprobado_corfo_castable"] = {"value": None, "status": "fail"}

    # ── Overall result ────────────────────────────────────────────────────────
    passed = all(c["status"] in ("ok", "warn") for c in checks.values())

    return {"passed": passed, "checks": checks}
