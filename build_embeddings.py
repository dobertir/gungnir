"""
build_embeddings.py
--------------------
Generates embeddings for all proyectos and stores them in proyectos_vec.
Works with both SQLite (local dev) and PostgreSQL (Railway production).

Usage:
    Local:    python build_embeddings.py
    Railway:  railway run python build_embeddings.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("ERROR: pip install sentence-transformers")
    sys.exit(1)

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_PATH = os.getenv("DB_PATH", "corfo_alimentos.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)


def get_conn():
    if USE_POSTGRES:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    print(f"Backend: {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")

    conn = get_conn()

    if USE_POSTGRES:
        cur = conn.cursor()
        cur.execute(
            "SELECT codigo, titulo_del_proyecto, objetivo_general_del_proyecto FROM proyectos"
        )
        rows = cur.fetchall()
        codigos = [r[0] for r in rows]
        texts   = [f"{r[1] or ''} {r[2] or ''}".strip() for r in rows]
    else:
        import sqlite3
        cur = conn.execute(
            "SELECT codigo, titulo_del_proyecto, objetivo_general_del_proyecto FROM proyectos"
        )
        rows = cur.fetchall()
        codigos = [r["codigo"] for r in rows]
        texts   = [f"{r['titulo_del_proyecto'] or ''} {r['objetivo_general_del_proyecto'] or ''}".strip() for r in rows]

    total = len(codigos)
    print(f"Proyectos encontrados: {total}")
    if total == 0:
        print("No hay proyectos. Abortando.")
        conn.close()
        return

    print(f"Cargando modelo '{MODEL_NAME}' ...")
    model = SentenceTransformer(MODEL_NAME)
    print("Modelo cargado.")

    print("Generando embeddings ...")
    t0 = time.perf_counter()
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("Almacenando vectores ...")
    if USE_POSTGRES:
        import psycopg2.extras
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS proyectos_vec (
                codigo TEXT PRIMARY KEY,
                vector BYTEA NOT NULL
            )
        """)
        conn.commit()
        cur.execute("DELETE FROM proyectos_vec")
        for i, (codigo, vec) in enumerate(zip(codigos, embeddings), start=1):
            blob = vec.astype("float32").tobytes()
            cur.execute(
                "INSERT INTO proyectos_vec (codigo, vector) VALUES (%s, %s) "
                "ON CONFLICT (codigo) DO UPDATE SET vector = EXCLUDED.vector",
                (codigo, psycopg2.Binary(blob)),
            )
            if i % 100 == 0 or i == total:
                print(f"\r{i}/{total}", end="", flush=True)
        conn.commit()
    else:
        conn.execute("DROP TABLE IF EXISTS proyectos_vec")
        conn.execute(
            "CREATE TABLE proyectos_vec (codigo TEXT PRIMARY KEY, vector BLOB NOT NULL)"
        )
        conn.commit()
        for i, (codigo, vec) in enumerate(zip(codigos, embeddings), start=1):
            blob = vec.astype("float32").tobytes()
            conn.execute(
                "INSERT INTO proyectos_vec (codigo, vector) VALUES (?, ?)", (codigo, blob)
            )
            if i % 100 == 0 or i == total:
                print(f"\r{i}/{total}", end="", flush=True)
        conn.commit()

    conn.close()
    elapsed = time.perf_counter() - t0
    print(f"\nIndexados {total} proyectos en {elapsed:.1f}s")


if __name__ == "__main__":
    main()
