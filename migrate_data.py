#!/usr/bin/env python3
"""
migrate_data.py — One-time data migration: corfo_alimentos.db → PostgreSQL (Railway)

Usage:
    DATABASE_URL=<railway_url> python migrate_data.py
    DATABASE_URL=<railway_url> python migrate_data.py --sqlite /path/to/corfo_alimentos.db
    DATABASE_URL=<railway_url> python migrate_data.py --dry-run

Prerequisites:
    1. PostgreSQL schema already created:
           psql $DATABASE_URL -f sync/schema_migrations/003_create_postgresql_schema.sql
    2. DATABASE_URL environment variable set (Railway provides this automatically)
    3. psycopg2-binary installed (already in requirements.txt)

Tables migrated (FK-safe order):
    organizations → users → proyectos → empresas → adjudicaciones → leads → _sync_log

Tables intentionally skipped:
    leads_old     — obsolete backup of pre-DOB-125 schema
    proyectos_vec — SQLite BLOB vector index, no PostgreSQL equivalent
    sqlite_sequence — SQLite internal metadata table

After running:
    Verify counts match (script prints them automatically).
    SERIAL sequences are reset so future INSERTs won't collide with migrated IDs.
"""

import argparse
import os
import sqlite3
import sys

import pandas as pd
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

# ── Migration plan ─────────────────────────────────────────────────────────────
# (sqlite_table, pg_table, text_to_numeric_cols, has_serial_id)
#
# text_to_numeric_cols: columns stored as TEXT in SQLite that are NUMERIC in PG.
# Empty strings are converted to None (NULL); valid numeric strings to float.
# has_serial_id: True when the table has an `id SERIAL PRIMARY KEY` that needs
# its sequence reset after bulk insert.

MIGRATION_PLAN = [
    ("organizations", "organizations", [],                                         True),
    ("users",         "users",         [],                                         True),
    ("proyectos",     "proyectos",     ["aprobado_corfo", "aprobado_privado",
                                        "aprobado_privado_pecuniario",
                                        "monto_consolidado_ley"],                  False),
    ("empresas",      "empresas",      [],                                         False),
    ("adjudicaciones","adjudicaciones",[],                                         False),
    ("leads",         "leads",         [],                                         True),
    ("_sync_log",     "_sync_log",     [],                                         True),
]

# Tables that exist in SQLite but must never be migrated
SKIP_TABLES = {"leads_old", "proyectos_vec", "sqlite_sequence"}


# ── Type coercions ─────────────────────────────────────────────────────────────

def _coerce_numeric_text(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Convert TEXT columns that become NUMERIC in PostgreSQL.
    Empty string / whitespace-only → None (NULL).
    Valid numeric string → float.
    Unparseable → None (NULL) with a warning.
    """
    for col in cols:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col].replace("", None), errors="coerce")
        bad = df[col].notna() & (df[col].astype(str).str.strip() != "") & converted.isna()
        if bad.any():
            print(f"  [WARN] {col}: {bad.sum()} values could not be parsed as numeric → NULL")
        df[col] = converted.where(converted.notna(), other=None)
    return df


def _coerce_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace pandas NaT / NaN with None so psycopg2 binds them as NULL.
    Covers both object-dtype columns (TEXT in SQLite) and datetime64 columns
    that pandas may infer from ISO timestamp strings.
    """
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].where(df[col].notna(), other=None)
    return df


# ── Core migration ─────────────────────────────────────────────────────────────

def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    sqlite_table: str,
    pg_table: str,
    text_to_numeric_cols: list[str],
    dry_run: bool = False,
) -> int:
    """
    Read all rows from sqlite_table, apply coercions, bulk-insert into pg_table.
    Returns number of rows migrated.
    """
    # Check the table exists in SQLite (organizations/users may not exist yet)
    exists = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (sqlite_table,)
    ).fetchone()
    if not exists:
        print(f"  [SKIP] {sqlite_table} — not found in SQLite (may not have been created yet)")
        return 0

    df = pd.read_sql_query(f'SELECT * FROM "{sqlite_table}"', sqlite_conn)
    if df.empty:
        print(f"  [SKIP] {sqlite_table} — 0 rows in SQLite")
        return 0

    # Apply type coercions
    df = _coerce_numeric_text(df, text_to_numeric_cols)
    df = _coerce_timestamps(df)

    row_count = len(df)

    if dry_run:
        print(f"  [DRY]  {sqlite_table} → {pg_table}: {row_count} rows (not inserted)")
        return row_count

    # Build INSERT using psycopg2.sql for safe identifier quoting
    # This handles columns with special chars like "año_adjudicacion"
    col_identifiers = [sql.Identifier(c) for c in df.columns]
    insert_sql = sql.SQL(
        "INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    ).format(
        table=sql.Identifier(pg_table),
        cols=sql.SQL(", ").join(col_identifiers),
    )

    # Convert DataFrame rows to list of tuples, replacing pandas NA with None
    rows = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    cur = pg_conn.cursor()
    psycopg2.extras.execute_values(cur, insert_sql, rows, page_size=500)
    pg_conn.commit()

    print(f"  [OK]   {sqlite_table} → {pg_table}: {row_count} rows migrated")
    return row_count


def reset_sequence(pg_conn, table: str, id_col: str = "id") -> None:
    """
    Reset the SERIAL sequence for a table so future INSERTs don't collide
    with the IDs imported from SQLite.
    """
    cur = pg_conn.cursor()
    # Get the sequence name (PostgreSQL naming convention: {table}_{col}_seq)
    cur.execute(
        sql.SQL(
            "SELECT pg_get_serial_sequence({table}, {col})"
        ).format(
            table=sql.Literal(table),
            col=sql.Literal(id_col),
        )
    )
    row = cur.fetchone()
    if not row or not row[0]:
        print(f"  [WARN] No sequence found for {table}.{id_col} — skipping reset")
        return

    seq_name = row[0]
    cur.execute(
        sql.SQL(
            "SELECT setval({seq}, COALESCE((SELECT MAX({col}) FROM {table}), 1))"
        ).format(
            seq=sql.Literal(seq_name),
            col=sql.Identifier(id_col),
            table=sql.Identifier(table),
        )
    )
    pg_conn.commit()
    print(f"  [SEQ]  {table}.{id_col} sequence reset")


def verify_counts(sqlite_conn: sqlite3.Connection, pg_conn) -> bool:
    """
    Compare row counts between SQLite and PostgreSQL for all migrated tables.
    Returns True if all counts match.
    """
    print("\n── Row count verification ──────────────────────────────────────")
    all_ok = True
    cur = pg_conn.cursor()

    for sqlite_table, pg_table, _, _ in MIGRATION_PLAN:
        exists = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (sqlite_table,)
        ).fetchone()
        if not exists:
            continue

        sqlite_count = sqlite_conn.execute(
            f'SELECT COUNT(*) FROM "{sqlite_table}"'
        ).fetchone()[0]

        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(pg_table)))
        pg_count = cur.fetchone()[0]

        status = "✓" if sqlite_count == pg_count else "✗ MISMATCH"
        print(f"  {status}  {pg_table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        if sqlite_count != pg_count:
            all_ok = False

    return all_ok


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate corfo_alimentos.db → PostgreSQL (one-time)"
    )
    parser.add_argument(
        "--sqlite",
        default=os.getenv("DB_PATH", "corfo_alimentos.db"),
        help="Path to the SQLite database file (default: corfo_alimentos.db)",
    )
    parser.add_argument(
        "--pg-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be migrated without writing to PostgreSQL",
    )
    args = parser.parse_args()

    if not args.pg_url and not args.dry_run:
        print("[ERROR] DATABASE_URL is not set. Export it or pass --pg-url.")
        sys.exit(1)

    if not os.path.exists(args.sqlite):
        print(f"[ERROR] SQLite file not found: {args.sqlite}")
        sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"[{mode}] Migrating {args.sqlite} → PostgreSQL")
    print(f"  SQLite:     {args.sqlite}")
    pg_display = (args.pg_url[:40] + "...") if args.pg_url else "(not set — dry-run only)"
    print(f"  PostgreSQL: {pg_display}")
    print()

    sqlite_conn = sqlite3.connect(args.sqlite)
    pg_conn = None if args.dry_run else psycopg2.connect(args.pg_url)

    try:
        print("── Migrating tables ────────────────────────────────────────────")
        total_rows = 0
        for sqlite_table, pg_table, numeric_cols, has_serial in MIGRATION_PLAN:
            rows = migrate_table(
                sqlite_conn, pg_conn,
                sqlite_table, pg_table, numeric_cols,
                dry_run=args.dry_run,
            )
            total_rows += rows

        if not args.dry_run:
            print("\n── Resetting SERIAL sequences ──────────────────────────────────")
            for sqlite_table, pg_table, _, has_serial in MIGRATION_PLAN:
                if has_serial:
                    reset_sequence(pg_conn, pg_table)

            all_ok = verify_counts(sqlite_conn, pg_conn)

            print()
            if all_ok:
                print(f"[OK] Migration complete — {total_rows} total rows migrated.")
                print()
                print("Next steps:")
                print("  1. Connect the Railway PostgreSQL plugin to your service")
                print("  2. Set DATABASE_URL in Railway service variables")
                print("  3. Deploy and run a test NL query via the app")
            else:
                print("[WARN] Some row counts do not match — review warnings above.")
                sys.exit(1)
        else:
            print(f"\n[DRY RUN] Would migrate {total_rows} total rows.")

    finally:
        sqlite_conn.close()
        if pg_conn:
            pg_conn.close()


if __name__ == "__main__":
    main()
