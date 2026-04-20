"""
build_embeddings.py
--------------------
Script de indexación único — genera embeddings para todos los proyectos y los
almacena en la tabla `proyectos_vec` de corfo_alimentos.db.

Uso:
    conda run -n work python build_embeddings.py

Requiere:
    pip install sentence-transformers
"""

import sys
import os
import sqlite3
import time

# ── Verificar dependencia antes de importar ───────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    print(
        "\nERROR: Dependencias faltantes.\n"
        "Instala los paquetes necesarios con:\n\n"
        "    pip install sentence-transformers\n"
    )
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corfo_alimentos.db")


def build_embeddings() -> None:
    print(f"Conectando a la base de datos: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # Leer proyectos — usar rowid como identificador único (la tabla no tiene columna id)
    cur = conn.execute(
        "SELECT rowid, titulo_del_proyecto, objetivo_general_del_proyecto FROM proyectos"
    )
    rows = cur.fetchall()
    total = len(rows)
    print(f"Proyectos encontrados: {total}")

    if total == 0:
        print("No hay proyectos en la base de datos. Abortando.")
        conn.close()
        return

    # Reconstruir tabla desde cero (full rebuild)
    conn.execute("DROP TABLE IF EXISTS proyectos_vec")
    conn.execute(
        "CREATE TABLE proyectos_vec (id INTEGER PRIMARY KEY, vector BLOB NOT NULL)"
    )
    conn.commit()
    print(f"Tabla proyectos_vec recreada.")

    # Cargar modelo
    print(f"Cargando modelo '{MODEL_NAME}' …")
    model = SentenceTransformer(MODEL_NAME)
    print("Modelo cargado.")

    # Generar embeddings
    t0 = time.perf_counter()
    texts = []
    rowids = []
    for rowid, titulo, objetivo in rows:
        text = f"{titulo or ''} {objetivo or ''}".strip()
        texts.append(text)
        rowids.append(rowid)

    print("Generando embeddings …")
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    # Insertar en la tabla con barra de progreso simple
    print("Almacenando vectores …")
    for i, (rowid, vec) in enumerate(zip(rowids, embeddings), start=1):
        blob = vec.astype("float32").tobytes()
        conn.execute("INSERT INTO proyectos_vec (id, vector) VALUES (?, ?)", (rowid, blob))
        if i % 100 == 0 or i == total:
            print(f"\r{i}/{total}", end="", flush=True)

    conn.commit()
    conn.close()

    elapsed = time.perf_counter() - t0
    print(f"\nIndexados {total} proyectos en {elapsed:.1f}s")


if __name__ == "__main__":
    build_embeddings()
