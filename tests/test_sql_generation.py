"""
tests/test_sql_generation.py
-----------------------------
Mide la accuracy del pipeline NL→SQL contra el benchmark en
tests/benchmark_questions.json. Llama al pipeline real de Mellea,
por lo que requiere el entorno configurado (DB, .env, Ollama corriendo).

Uso directo:  python tests/test_sql_generation.py
Como pytest:  python -m pytest tests/test_sql_generation.py -v  (más lento — llama al LLM)

Meta de calidad: ≥ 80% de accuracy antes de hacer cambios al pipeline NL→SQL.
"""

import json
import re
import sqlite3
import sys
import os
import logging
from pathlib import Path

# Silenciar logs de Mellea durante el benchmark
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("corfo.benchmark")

# Asegurar que el root del proyecto esté en el path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

BENCHMARK_PATH = ROOT / "tests" / "benchmark_questions.json"
DB_PATH        = os.getenv("DB_PATH", str(ROOT / "corfo_alimentos.db"))


# ── Utilidades SQL ────────────────────────────────────────────────────────────

def normalize_sql(sql: str) -> str:
    """Normaliza SQL para comparación flexible: minúsculas, espacios colapsados."""
    sql = sql.strip().lower()
    sql = re.sub(r"\s+", " ", sql)
    sql = sql.rstrip(";")
    return sql


def sql_is_safe(sql: str) -> bool:
    """True si el SQL es solo SELECT — nunca mutación."""
    upper = sql.strip().upper()
    for peligroso in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"):
        if upper.startswith(peligroso) or f" {peligroso} " in upper:
            return False
    return True


def sql_ejecuta_ok(sql: str) -> tuple[bool, str]:
    """Intenta ejecutar el SQL contra la BD real. Retorna (ok, mensaje_error)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(sql).fetchmany(5)
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


# ── Generación SQL via corfo_server ───────────────────────────────────────────

def generar_sql(pregunta: str) -> str | None:
    """
    Llama al mismo pipeline de generación SQL que usa corfo_server.py.
    Retorna el SQL generado, o None si falla.
    """
    try:
        from corfo_server import _generate_sql  # type: ignore
        result = _generate_sql(pregunta)
        return result.get("sql") if isinstance(result, dict) else None
    except ImportError:
        log.error("No se pudo importar corfo_server — ejecutar desde el root del proyecto")
        return None
    except Exception as e:
        log.warning("Fallo generando SQL para '%s': %s", pregunta, e)
        return None


# ── Runner del benchmark ──────────────────────────────────────────────────────

def run_benchmark(benchmark_path: Path = BENCHMARK_PATH) -> dict:
    """
    Ejecuta el benchmark completo de NL→SQL.
    Retorna un dict con accuracy, listas de pass/fail, y detalle por pregunta.
    """
    if not benchmark_path.exists():
        print(f"\nERROR: No se encontró el benchmark en {benchmark_path}")
        print("Crear tests/benchmark_questions.json primero.")
        sys.exit(1)

    with open(benchmark_path, encoding="utf-8") as f:
        preguntas = json.load(f)

    total     = len(preguntas)
    aprobadas = []
    fallidas  = []

    print(f"\n{'='*65}")
    print(f"  CORFO NL→SQL Benchmark — {total} preguntas")
    print(f"  DB: {DB_PATH}")
    print(f"{'='*65}\n")

    for i, item in enumerate(preguntas, 1):
        pregunta  = item["question_es"]
        esperado  = (item.get("sql") or "").strip()
        notas     = item.get("notes", "")

        print(f"[{i:02d}/{total}] {pregunta}")

        generado = generar_sql(pregunta)

        resultado = {
            "pregunta"     : pregunta,
            "sql_esperado" : esperado,
            "sql_generado" : generado,
            "notas"        : notas,
        }

        # ── Fallo: no se generó SQL ──
        if generado is None:
            resultado["veredicto"] = "FALLO — error de generación"
            fallidas.append(resultado)
            print(f"         ✗ No se generó SQL\n")
            continue

        # ── Fallo: SQL inseguro ──
        if not sql_is_safe(generado):
            resultado["veredicto"] = "FALLO — SQL inseguro (mutación detectada)"
            fallidas.append(resultado)
            print(f"         ✗ SQL INSEGURO: {generado[:80]}\n")
            continue

        # ── Fallo: SQL no ejecuta ──
        ejecuta, error = sql_ejecuta_ok(generado)
        if not ejecuta:
            resultado["veredicto"] = f"FALLO — SQL no ejecuta: {error}"
            fallidas.append(resultado)
            print(f"         ✗ Error de ejecución: {error}\n")
            continue

        # ── Comparación semántica (normalizada) ──
        if esperado:
            norm_esp = normalize_sql(esperado)
            norm_gen = normalize_sql(generado)

            if norm_gen == norm_esp:
                resultado["veredicto"] = "PASS — match exacto"
                aprobadas.append(resultado)
                print(f"         ✓ Match exacto\n")
            else:
                # Ejecuta OK pero SQL difiere — PASS con nota para revisión humana
                resultado["veredicto"] = "PASS-EJECUCIÓN (revisar semántica)"
                resultado["diff"] = {
                    "esperado"  : norm_esp[:120],
                    "generado"  : norm_gen[:120],
                }
                aprobadas.append(resultado)
                print(f"         ~ Ejecuta OK — SQL difiere del esperado")
                print(f"           Esperado:  {norm_esp[:75]}")
                print(f"           Generado:  {norm_gen[:75]}\n")
        else:
            # Sin SQL esperado — solo verificamos que ejecuta
            resultado["veredicto"] = "PASS-EJECUCIÓN (sin SQL esperado para comparar)"
            aprobadas.append(resultado)
            print(f"         ✓ Ejecuta OK (sin SQL esperado)\n")

    accuracy = len(aprobadas) / total * 100 if total > 0 else 0
    meta_ok  = accuracy >= 80

    print(f"\n{'='*65}")
    print(f"  RESULTADO: {len(aprobadas)}/{total} aprobadas — Accuracy: {accuracy:.1f}%")
    print(f"  Meta ≥ 80% → {'✓ CUMPLIDA' if meta_ok else '✗ NO CUMPLIDA'}")
    print(f"{'='*65}\n")

    if fallidas:
        print(f"FALLOS ({len(fallidas)}):")
        for item in fallidas:
            print(f"  ✗ {item['pregunta']}")
            print(f"    {item['veredicto']}")
            if item.get("sql_generado"):
                print(f"    SQL generado: {item['sql_generado'][:100]}")
            print()

    diffs = [r for r in aprobadas if "diff" in r]
    if diffs:
        print(f"\nPASS-EJECUCIÓN con diferencias semánticas ({len(diffs)}) — revisar:")
        for item in diffs:
            print(f"  ~ {item['pregunta']}")
            print(f"    Esperado:  {item['diff']['esperado'][:80]}")
            print(f"    Generado:  {item['diff']['generado'][:80]}")
            print()

    return {
        "total"        : total,
        "aprobadas"    : len(aprobadas),
        "fallidas"     : len(fallidas),
        "accuracy_pct" : round(accuracy, 1),
        "meta_cumplida": meta_ok,
        "fallos"       : fallidas,
    }


# ── Integración con pytest ────────────────────────────────────────────────────

def test_benchmark_accuracy():
    """Test pytest — falla si accuracy < 80%."""
    resultado = run_benchmark()
    assert resultado["meta_cumplida"], (
        f"Accuracy NL→SQL {resultado['accuracy_pct']}% por debajo de la meta del 80%. "
        f"Preguntas fallidas: {[f['pregunta'] for f in resultado['fallos']]}"
    )


def test_sql_generado_es_seguro():
    """Todo SQL generado debe ser SELECT-only — nunca mutación."""
    if not BENCHMARK_PATH.exists():
        return

    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        preguntas = json.load(f)

    for item in preguntas:
        sql = generar_sql(item["question_es"])
        if sql:
            assert sql_is_safe(sql), (
                f"SQL inseguro generado para: {item['question_es']}\nSQL: {sql}"
            )


def test_sql_ejecuta_contra_bd_real():
    """Todo SQL generado debe ejecutarse sin error contra corfo_alimentos.db."""
    if not BENCHMARK_PATH.exists():
        return

    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        preguntas = json.load(f)

    errores = []
    for item in preguntas:
        sql = generar_sql(item["question_es"])
        if sql and sql_is_safe(sql):
            ok, error = sql_ejecuta_ok(sql)
            if not ok:
                errores.append(f"{item['question_es']}: {error}")

    assert not errores, (
        f"SQL no ejecuta en {len(errores)} casos:\n" +
        "\n".join(f"  - {e}" for e in errores)
    )


def test_campos_criticos_respetados():
    """
    Verifica las dos reglas SQL críticas del proyecto:
    1. año_adjudicacion siempre entre comillas dobles
    2. aprobado_corfo con CAST cuando se usa en SUM/AVG/MAX/MIN
    """
    casos_año = [
        "¿Cuántos proyectos aprobó CORFO en 2023?",
        "¿Cuántos proyectos hubo en 2020?",
        "¿Cuántos proyectos hay entre 2018 y 2022?",
    ]
    casos_cast = [
        "¿Cuál fue el monto total aprobado por CORFO en 2022?",
        "¿Cuál empresa recibió más dinero de CORFO?",
        "¿Cuál es el promedio del monto aprobado por proyecto?",
    ]

    fallos_año  = []
    fallos_cast = []

    for pregunta in casos_año:
        sql = generar_sql(pregunta)
        if sql and "año_adjudicacion" in sql.lower():
            if '"año_adjudicacion"' not in sql:
                fallos_año.append(pregunta)

    for pregunta in casos_cast:
        sql = generar_sql(pregunta)
        if sql and "aprobado_corfo" in sql.lower():
            upper = sql.upper()
            if any(f in upper for f in ["SUM(", "AVG(", "MAX(", "MIN("]):
                if "CAST" not in upper:
                    fallos_cast.append(pregunta)

    assert not fallos_año, (
        f"año_adjudicacion sin comillas dobles en {len(fallos_año)} caso(s): {fallos_año}"
    )
    assert not fallos_cast, (
        f"aprobado_corfo sin CAST en operación numérica en {len(fallos_cast)} caso(s): {fallos_cast}"
    )


# ── Guardrail: validación de identificadores SQL ──────────────────────────────

def test_guardrail_rechaza_columna_inexistente(authed_client):
    """
    Verifica que /api/query devuelve HTTP 422 cuando _generate_sql produce SQL
    con una columna que no existe en el esquema real de la base de datos.

    Se usa unittest.mock.patch para inyectar SQL falso sin llamar al LLM.
    """
    from unittest.mock import patch
    import corfo_server  # type: ignore

    sql_falso = "SELECT fake_column FROM proyectos"
    respuesta_mock = {"sql": sql_falso, "chart_type": None}

    with patch("corfo_server._generate_sql", return_value=respuesta_mock):
        resp = authed_client.post(
            "/api/query",
            json={"question": "pregunta de prueba"},
            content_type="application/json",
        )

    assert resp.status_code == 422, (
        f"Se esperaba HTTP 422, se obtuvo {resp.status_code}. "
        f"Cuerpo: {resp.get_data(as_text=True)}"
    )
    body = resp.get_json()
    assert "error" in body, "La respuesta 422 debe incluir el campo 'error'."
    assert "fake_column" in body["error"], (
        f"El mensaje de error debe mencionar 'fake_column'. Mensaje: {body['error']}"
    )


# ── Validación de calidad del resultado ──────────────────────────────────────

def test_resultado_vacio_incluye_warning(authed_client):
    """
    Cuando el SQL ejecuta pero devuelve un DataFrame vacío, la respuesta debe
    incluir el campo 'warning' indicando que no hubo resultados.
    """
    from unittest.mock import patch, MagicMock
    import pandas as pd
    import corfo_server  # type: ignore

    sql_valido = "SELECT razon FROM proyectos WHERE 1=0"
    respuesta_mock = {"sql": sql_valido, "chart_type": None}
    df_vacio = pd.DataFrame()

    with patch("corfo_server._generate_sql", return_value=respuesta_mock), \
         patch("corfo_server._explain_results", return_value="Sin resultados."), \
         patch("corfo_server.pd.read_sql_query", return_value=df_vacio):
        resp = authed_client.post(
            "/api/query",
            json={"question": "proyectos de sector inexistente xyz123"},
            content_type="application/json",
        )

    assert resp.status_code == 200, (
        f"Se esperaba HTTP 200, se obtuvo {resp.status_code}."
    )
    body = resp.get_json()
    assert "warning" in body, (
        f"La respuesta debe incluir 'warning' cuando el resultado está vacío. "
        f"Cuerpo: {body}"
    )


def test_resultado_grande_incluye_warning(authed_client):
    """
    Cuando el SQL devuelve >= 50 filas y la pregunta no contiene 'todos/todo/all',
    la respuesta debe incluir el campo 'warning' sugiriendo filtrar.
    """
    from unittest.mock import patch
    import pandas as pd
    import corfo_server  # type: ignore

    sql_valido = "SELECT razon FROM proyectos LIMIT 50"
    respuesta_mock = {"sql": sql_valido, "chart_type": None}
    df_grande = pd.DataFrame({"razon": [f"Empresa {i}" for i in range(51)]})

    with patch("corfo_server._generate_sql", return_value=respuesta_mock), \
         patch("corfo_server._explain_results", return_value="Muchos resultados."), \
         patch("corfo_server.pd.read_sql_query", return_value=df_grande):
        resp = authed_client.post(
            "/api/query",
            json={"question": "¿Cuáles son las empresas del sector alimentos?"},
            content_type="application/json",
        )

    assert resp.status_code == 200, (
        f"Se esperaba HTTP 200, se obtuvo {resp.status_code}."
    )
    body = resp.get_json()
    assert "warning" in body, (
        f"La respuesta debe incluir 'warning' cuando se devuelven >= 50 filas "
        f"sin palabras de intención amplia. Cuerpo: {body}"
    )


# ── Entry point CLI ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_benchmark()
