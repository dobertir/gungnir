"""
sync/sector_normalizacion.py
-----------------------------
Tabla de normalización sector_canonico(sector_raw, sector_display).

sector_raw    : valor exacto almacenado en proyectos.sector_economico (fuente: datainnovacion.cl)
sector_display: forma canónica mostrada al usuario

Solo se fusionan variantes puramente ortográficas (tildes, "de" vs sin "de",
singular/plural). Sectores semánticamente distintos se mantienen separados.

Valores de referencia relevados el 2026-04-29 — 49 variantes observadas.
"""

import logging

log = logging.getLogger("corfo.sync")

# ── Mapa de normalización ─────────────────────────────────────────────────────
# Clave   : sector_raw (valor tal como llega de la API / está en proyectos)
# Valor   : sector_display (forma canónica que ve el usuario)

SECTOR_CANONICO: dict[str, str] = {
    # Agrícola — 3 variantes ortográficas del mismo sector
    "Agrícola (excepto cultivo de uvas)":  "Agrícola (excepto vitivinícola)",
    "Agrícola (excepto vitivinicola)":     "Agrícola (excepto vitivinícola)",
    "Agrícola (excepto vitivinícola)":     "Agrícola (excepto vitivinícola)",

    # Alimentos — 3 variantes ortográficas del mismo sector
    "Alimentos (excepto producción de vino y derivados)": "Alimentos (excepto vitivinícola)",
    "Alimentos (excepto vitivinicola)":                   "Alimentos (excepto vitivinícola)",
    "Alimentos (excepto vitivinícola)":                   "Alimentos (excepto vitivinícola)",

    # Farmacéutica — falta tilde
    "Farmaceutica": "Farmacéutica",
    "Farmacéutica": "Farmacéutica",

    # Química — falta tilde en sub-frase
    "Química, caucho y plásticos (excepto industria farmaceutica)":  "Química, caucho y plásticos (excepto industria farmacéutica)",
    "Química, caucho y plásticos (excepto industria farmacéutica)":  "Química, caucho y plásticos (excepto industria farmacéutica)",

    # Industria creativa — "de esparcimiento" vs "y esparcimiento"
    "Industria creativa y de esparcimiento": "Industria creativa y esparcimiento",
    "Industria creativa y esparcimiento":    "Industria creativa y esparcimiento",

    # Inmobiliario — plural vs singular
    "Inmobiliarias": "Inmobiliario",
    "Inmobiliario":  "Inmobiliario",

    # ── Mapeos identidad (sin normalización necesaria) ────────────────────────
    "Asociaciones y organizaciones no empresariales ni gubernamentales": "Asociaciones y organizaciones no empresariales ni gubernamentales",
    "Banca y sector financiero":                          "Banca y sector financiero",
    "Biotecnológico":                                     "Biotecnológico",
    "Comercio y retail":                                  "Comercio y retail",
    "Construcción":                                       "Construcción",
    "Educación":                                          "Educación",
    "Educación y servicios conexos":                      "Educación y servicios conexos",
    "Energético":                                         "Energético",
    "Finanzas":                                           "Finanzas",
    "Forestal":                                           "Forestal",
    "Ganadero":                                           "Ganadero",
    "Gestión de desechos":                                "Gestión de desechos",
    "Gestión de desechos y Valorizacion de residuos":     "Gestión de desechos y Valorización de residuos",
    "Gestión de desechos y Valorización de residuos":     "Gestión de desechos y Valorización de residuos",
    "Logística y Transporte":                             "Logística y Transporte",
    "Manufactura de maquinaria y equipos (Metalmecánico)": "Manufactura de maquinaria y equipos (Metalmecánico)",
    "Manufactura de metales básicos":                     "Manufactura de metales básicos",
    "Manufactura de no metálicos":                        "Manufactura de no metálicos",
    "Medioambiente":                                      "Medioambiente",
    "Minería y metalurgia extractiva":                    "Minería y metalurgia extractiva",
    "Multisectorial":                                     "Multisectorial",
    "Otras industrias manufactureras":                    "Otras industrias manufactureras",
    "Otros servicios":                                    "Otros servicios",
    "Otros servicios empresariales":                      "Otros servicios empresariales",
    "Pesca y acuicultura":                                "Pesca y acuicultura",
    "Recursos Hídricos":                                  "Recursos Hídricos",
    "Salud y Farmacéutica (en humanos)":                  "Salud y Farmacéutica (en humanos)",
    "Salud y asistencia social":                          "Salud y asistencia social",
    "Sector público":                                     "Sector público",
    "Servicios de ingeniería o de conocimiento":          "Servicios de ingeniería o de conocimiento",
    "Servicios empresariales administrativos y de apoyo": "Servicios empresariales administrativos y de apoyo",
    "Tecnologías de la información":                      "Tecnologías de la información",
    "Telecomunicaciones":                                 "Telecomunicaciones",
    "Telecomunicaciones y tecnologías de la información": "Telecomunicaciones y tecnologías de la información",
    "Turismo":                                            "Turismo",
    "Vitivinícola":                                       "Vitivinícola",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_pg(conn) -> bool:
    """True si conn es una conexión psycopg2 (PostgreSQL)."""
    import sqlite3
    return not isinstance(conn, sqlite3.Connection)


# ── Schema ────────────────────────────────────────────────────────────────────

def ensure_sector_canonico_table(conn) -> None:
    """Crea sector_canonico si no existe. Funciona en PostgreSQL y SQLite."""
    ddl = """
        CREATE TABLE IF NOT EXISTS sector_canonico (
            sector_raw     TEXT PRIMARY KEY,
            sector_display TEXT NOT NULL
        )
    """
    cur = conn.cursor()
    cur.execute(ddl)
    conn.commit()
    log.debug("ensure_sector_canonico_table: tabla verificada")


# ── Rebuild ───────────────────────────────────────────────────────────────────

def rebuild_sector_canonico(conn) -> int:
    """
    Puebla sector_canonico con los mapeos de SECTOR_CANONICO más cualquier
    valor nuevo encontrado en proyectos.sector_economico (mapeo identidad).

    Usa INSERT OR REPLACE / ON CONFLICT DO UPDATE — idempotente.
    Retorna el número de filas procesadas.
    """
    pg = _is_pg(conn)
    cur = conn.cursor()

    # Recoger valores distintos actuales en proyectos para detectar nuevos.
    # conn.cursor() devuelve tuplas en ambos drivers (psycopg2 default y sqlite3).
    cur.execute(
        "SELECT DISTINCT sector_economico FROM proyectos "
        "WHERE sector_economico IS NOT NULL"
    )
    raw_in_db: set[str] = {r[0] for r in cur.fetchall()}

    # Construir mapa completo: hardcoded + identidad para desconocidos
    full_map: dict[str, str] = dict(SECTOR_CANONICO)
    for raw in raw_in_db:
        if raw not in full_map:
            log.warning("sector_normalizacion: valor nuevo sin mapeo → identidad: %r", raw)
            full_map[raw] = raw

    rows = list(full_map.items())

    if pg:
        from psycopg2.extras import execute_values
        sql = """
            INSERT INTO sector_canonico (sector_raw, sector_display) VALUES %s
            ON CONFLICT (sector_raw) DO UPDATE SET sector_display = EXCLUDED.sector_display
        """
        execute_values(cur, sql, rows, page_size=200)
        conn.commit()
    else:
        sql = "INSERT OR REPLACE INTO sector_canonico (sector_raw, sector_display) VALUES (?, ?)"
        conn.executemany(sql, rows)
        conn.commit()

    log.info("rebuild_sector_canonico: %d mapeos cargados", len(rows))
    return len(rows)
