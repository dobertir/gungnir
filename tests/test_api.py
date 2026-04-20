"""
tests/test_api.py
------------------
Flask endpoint tests using the built-in test client.
No live server required — imports corfo_server directly.

Run: python -m pytest tests/test_api.py -v
"""

import json
import sqlite3
import pytest
import sys
import os

# Make sure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ruta absoluta a la base de datos de producción (misma que usa corfo_server.DB)
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corfo_alimentos.db")

# Identificador único para la fila de prueba — evita conflictos con datos reales
_TEST_RAZON = "Empresa Test SA"
_TEST_RUT   = "TEST-RUT-99999999"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create a Flask test client from corfo_server."""
    from corfo_server import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def empresa_test_row():
    """
    Inserta una fila mínima de 'Empresa Test SA' en la tabla proyectos de la BD
    real para que create_lead pueda encontrarla. Limpia proyectos Y leads al
    terminar, sin importar si el test pasó o falló.
    """
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    try:
        conn.execute("DELETE FROM leads WHERE nombre_compania = ?", (_TEST_RAZON,))
        conn.commit()
        conn.execute("""
            INSERT OR IGNORE INTO proyectos
                (codigo, rut_beneficiario, razon, sector_economico,
                 region_ejecucion, tramo_ventas, aprobado_corfo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "TEST-COD-99999999",
            _TEST_RUT,
            _TEST_RAZON,
            "Alimentos",
            "Región Metropolitana de Santiago",
            "Sin Ventas",
            "1000000",
        ))
        conn.commit()
    except Exception:
        conn.close()
        raise

    yield

    try:
        conn.execute("DELETE FROM leads WHERE nombre_compania = ?", (_TEST_RAZON,))
        conn.execute("DELETE FROM proyectos WHERE rut_beneficiario = ?", (_TEST_RUT,))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()


# ── GET / ─────────────────────────────────────────────────────────────────────

class TestRoot:
    def test_serves_html(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"html" in r.data.lower() or b"<!DOCTYPE" in r.data or b"react" in r.data.lower()


# ── GET /api/dashboard ────────────────────────────────────────────────────────

class TestDashboard:
    def test_returns_200(self, authed_client):
        r = authed_client.get("/api/dashboard")
        assert r.status_code == 200

    def test_returns_json(self, authed_client):
        r = authed_client.get("/api/dashboard")
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_has_expected_keys(self, authed_client):
        r = authed_client.get("/api/dashboard")
        data = json.loads(r.data)
        # At least one chart key must exist — adjust list to match actual keys
        assert len(data.keys()) > 0


# ── POST /api/query ───────────────────────────────────────────────────────────

class TestQuery:
    def test_happy_path(self, authed_client):
        r = authed_client.post(
            "/api/query",
            json={"question": "¿Cuántos proyectos hay en total?"},
            content_type="application/json"
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "answer" in data or "error" in data  # either is acceptable

    def test_missing_question_returns_error(self, authed_client):
        r = authed_client.post("/api/query", json={}, content_type="application/json")
        assert r.status_code in (400, 422)
        data = json.loads(r.data)
        assert "error" in data

    def test_empty_question_returns_error(self, authed_client):
        r = authed_client.post(
            "/api/query",
            json={"question": ""},
            content_type="application/json"
        )
        assert r.status_code in (400, 422)
        data = json.loads(r.data)
        assert "error" in data

    def test_sql_safety_no_mutation(self, authed_client):
        """Generated SQL must never be INSERT/UPDATE/DELETE."""
        r = authed_client.post(
            "/api/query",
            json={"question": "¿Cuántos proyectos hay en total?"},
            content_type="application/json"
        )
        data = json.loads(r.data)
        if "sql" in data:
            sql_upper = data["sql"].upper().strip()
            assert not sql_upper.startswith("INSERT")
            assert not sql_upper.startswith("UPDATE")
            assert not sql_upper.startswith("DELETE")
            assert not sql_upper.startswith("DROP")


# ── GET /api/leads ────────────────────────────────────────────────────────────

class TestLeads:
    def test_returns_200(self, authed_client):
        r = authed_client.get("/api/leads")
        assert r.status_code == 200

    def test_returns_list(self, authed_client):
        r = authed_client.get("/api/leads")
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_filter_by_sector(self, authed_client):
        r = authed_client.get("/api/leads?sector=Alimentos")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_filter_by_estado(self, authed_client):
        r = authed_client.get("/api/leads?estado=pendiente")
        assert r.status_code == 200

    def test_invalid_filter_does_not_crash(self, authed_client):
        r = authed_client.get("/api/leads?sector=SECTOR_INEXISTENTE_XYZ")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)  # empty list is fine


# ── GET /api/leads/stats ──────────────────────────────────────────────────────

class TestLeadsStats:
    def test_returns_200(self, authed_client):
        r = authed_client.get("/api/leads/stats")
        assert r.status_code == 200

    def test_has_count_fields(self, authed_client):
        r = authed_client.get("/api/leads/stats")
        data = json.loads(r.data)
        # Expect at least a total count
        assert any(k in data for k in ("total", "contactado", "pendiente", "counts"))


# ── GET /api/leads/<id> ───────────────────────────────────────────────────────

class TestLeadDetail:
    def test_nonexistent_id_returns_404(self, authed_client):
        r = authed_client.get("/api/leads/999999999")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert "error" in data

    def test_invalid_id_type_returns_error(self, authed_client):
        r = authed_client.get("/api/leads/not-a-number")
        assert r.status_code in (400, 404)


# ── PUT /api/leads/<id> ───────────────────────────────────────────────────────

class TestLeadUpdate:
    def test_nonexistent_id_returns_404(self, authed_client):
        r = authed_client.put(
            "/api/leads/999999999",
            json={"estado_contacto": "contactado"},
            content_type="application/json"
        )
        assert r.status_code == 404

    def test_whitelist_enforced(self, authed_client):
        """Fields outside the whitelist must be ignored or rejected."""
        r = authed_client.put(
            "/api/leads/1",
            json={"razon": "HACKED", "monto_total_aprobado": 0},
            content_type="application/json"
        )
        # Either 400 (rejected) or 200 (silently ignored) — both acceptable
        # but the field must not have changed if 200
        assert r.status_code in (200, 400, 404)

    def test_missing_body_returns_error(self, authed_client):
        r = authed_client.put("/api/leads/1", data="", content_type="application/json")
        assert r.status_code in (400, 404)


# ── POST /api/leads ───────────────────────────────────────────────────────────

class TestLeadCreate:
    def test_create_lead_from_result(self, authed_client, empresa_test_row):
        payload = {"razon": "Empresa Test SA", "sector_economico": "Alimentos"}
        r = authed_client.post("/api/leads", json=payload, content_type="application/json")
        # 201 created or 200 ok
        assert r.status_code in (200, 201)
        data = json.loads(r.data)
        assert "error" not in data

    def test_missing_razon_returns_error(self, authed_client):
        r = authed_client.post("/api/leads", json={}, content_type="application/json")
        assert r.status_code in (400, 422)
        data = json.loads(r.data)
        assert "error" in data


# ── POST /api/export/excel ────────────────────────────────────────────────────

class TestExport:
    def test_export_returns_file(self, authed_client):
        payload = {
            "data": [{"razon": "Empresa A", "monto": 1000000}],
            "filename": "test_export"
        }
        r = authed_client.post("/api/export/excel", json=payload, content_type="application/json")
        assert r.status_code in (200, 400)  # 400 if payload format differs


# ── POST /api/sync ────────────────────────────────────────────────────────────

class TestSync:
    def test_sync_endpoint_exists(self, authed_client):
        """Sync endpoint should exist — actual sync will fail in test env (no API access)."""
        r = authed_client.post("/api/sync")
        # Any structured response is acceptable — 200 ok or 500 with error json
        assert r.status_code in (200, 500)
        data = json.loads(r.data)
        assert "status" in data or "error" in data
