"""
001_add_org_user_tables.py — Migración: organizaciones y usuarios en BD

Crea las tablas `organizations` y `users` en corfo_alimentos.db y las puebla
con los datos del archivo .env (ADMIN_USERNAME, ADMIN_PASSWORD, etc.).

Uso:
    python sync/schema_migrations/001_add_org_user_tables.py

Es idempotente — se puede ejecutar múltiples veces sin efectos secundarios.
"""

import os
import sqlite3
import sys

# Allow running from any working directory
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(_BASE_DIR, ".env"))

from werkzeug.security import generate_password_hash

DB = os.path.join(_BASE_DIR, "corfo_alimentos.db")


CREATE_ORGANIZATIONS = """
CREATE TABLE IF NOT EXISTS organizations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    slug       TEXT NOT NULL UNIQUE,
    plan       TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id        INTEGER NOT NULL REFERENCES organizations(id),
    username      TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'viewer',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(org_id, username)
);
"""


def _seed_organization(cur: sqlite3.Cursor) -> int:
    """Inserta la organización predeterminada si no existe. Retorna su id."""
    cur.execute("SELECT id FROM organizations WHERE slug = 'default'")
    row = cur.fetchone()
    if row:
        print(f"[OMITIDO] Organización 'default' ya existe (id={row[0]}).")
        return row[0]

    cur.execute(
        "INSERT INTO organizations (name, slug, plan) VALUES (?, ?, ?)",
        ("Default", "default", "free"),
    )
    org_id = cur.lastrowid
    print(f"[CREADO]  Organización 'default' (id={org_id}).")
    return org_id


def _seed_user(cur: sqlite3.Cursor, org_id: int, username: str, password: str, role: str) -> None:
    """Inserta un usuario si no existe en esa organización."""
    cur.execute(
        "SELECT id FROM users WHERE org_id = ? AND username = ?",
        (org_id, username),
    )
    if cur.fetchone():
        print(f"[OMITIDO] Usuario '{username}' ya existe en org_id={org_id}.")
        return

    # .env must contain plaintext passwords; this script always hashes them.
    # If .env already stores a werkzeug hash, do NOT run this migration —
    # doing so would double-hash the value and make login impossible.
    password_hash = generate_password_hash(password)

    cur.execute(
        "INSERT INTO users (org_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
        (org_id, username, password_hash, role),
    )
    print(f"[CREADO]  Usuario '{username}' con rol '{role}' (org_id={org_id}).")


def run_migration() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    admin_role_raw = os.getenv("ADMIN_ROLE", "admin").strip().lower()
    admin_role = admin_role_raw if admin_role_raw in {"admin", "viewer"} else "admin"

    viewer_username = os.getenv("VIEWER_USERNAME", "").strip()
    viewer_password = os.getenv("VIEWER_PASSWORD", "").strip()

    if not admin_username or not admin_password:
        print("[ERROR] ADMIN_USERNAME y/o ADMIN_PASSWORD no están definidos en .env. Abortando.")
        sys.exit(1)

    conn = sqlite3.connect(DB)
    try:
        cur = conn.cursor()

        # 1. Crear tablas
        cur.execute(CREATE_ORGANIZATIONS)
        cur.execute(CREATE_USERS)
        print("[OK]     Tablas 'organizations' y 'users' verificadas/creadas.")

        # 2. Organización predeterminada
        org_id = _seed_organization(cur)

        # 3. Usuario admin
        _seed_user(cur, org_id, admin_username, admin_password, admin_role)

        # 4. Usuario viewer (opcional)
        if viewer_username and viewer_password:
            _seed_user(cur, org_id, viewer_username, viewer_password, "viewer")
        else:
            print("[INFO]   VIEWER_USERNAME/VIEWER_PASSWORD no configurados — se omite usuario viewer.")

        conn.commit()
        print("[LISTO]  Migración completada exitosamente.")
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR]  La migración falló y se revirtió: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
