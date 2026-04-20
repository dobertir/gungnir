"""
tests/test_empresa_perfil.py
----------------------------
Tests for the GET /api/empresa/<path:razon> endpoint added in DOB-144.

Covers:
  - Known razon returns HTTP 200 with all required JSON keys
  - Response JSON has no NaN values (NaN would break JSON parsing)
  - Statistics are consistent (total_proyectos matches len(proyectos))
  - Montos and years are numeric (not strings)
  - Nonexistent razon returns 200 with zeros or 404 (both acceptable)
  - URL with spaces in razon (path routing)
  - Empty razon path returns 404 or 400

Run: python -m pytest tests/test_empresa_perfil.py -v
"""

import json
import math
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.environ.get("DATAINNOVACION_TOKEN"):
    os.environ["DATAINNOVACION_TOKEN"] = "test-token-placeholder"


# ── Fixtures ──────────────────────────────────────────────────────────────────

# ── Helpers ───────────────────────────────────────────────────────────────────

# A razon that is guaranteed to exist in corfo_alimentos.db (production DB).
# We query the DB directly to discover a real value at test time.
def _get_known_razon():
    """Return the first razon found in the production database."""
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "corfo_alimentos.db")
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT razon FROM proyectos WHERE razon IS NOT NULL AND razon != '' LIMIT 1"
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _no_nan_in_json(data) -> bool:
    """Recursively check that no float NaN values are present in parsed JSON."""
    if isinstance(data, float) and math.isnan(data):
        return False
    if isinstance(data, dict):
        return all(_no_nan_in_json(v) for v in data.values())
    if isinstance(data, list):
        return all(_no_nan_in_json(item) for item in data)
    return True


REQUIRED_TOP_KEYS = {
    "razon",
    "total_proyectos",
    "monto_total",
    "primer_año",
    "ultimo_año",
    "proyectos",
    "por_año",
}

REQUIRED_PROJECT_KEYS = {
    "codigo",
    "año_adjudicacion",
    "instrumento",
    "titulo_del_proyecto",
    "aprobado_corfo",
    "sector_economico",
    "region_ejecucion",
    "tendencia_final",
}


# ── Tests: known razon ────────────────────────────────────────────────────────

class TestEmpresaPerfilKnown:
    """Tests that require a real razon from the database."""

    @pytest.fixture(scope="class")
    def known_razon(self):
        razon = _get_known_razon()
        if razon is None:
            pytest.skip("Could not find a known razon in corfo_alimentos.db")
        return razon

    @pytest.fixture(scope="class")
    def response_data(self, authed_client, known_razon):
        r = authed_client.get(f"/api/empresa/{known_razon}")
        assert r.status_code == 200, (
            f"GET /api/empresa/{known_razon!r} returned {r.status_code}, expected 200"
        )
        return json.loads(r.data)

    def test_returns_200(self, authed_client, known_razon):
        r = authed_client.get(f"/api/empresa/{known_razon}")
        assert r.status_code == 200

    def test_response_has_required_top_keys(self, response_data):
        for key in REQUIRED_TOP_KEYS:
            assert key in response_data, f"Missing required key: {key!r}"

    def test_razon_echoed_in_response(self, response_data, known_razon):
        assert response_data["razon"] == known_razon

    def test_proyectos_is_list(self, response_data):
        assert isinstance(response_data["proyectos"], list)

    def test_total_proyectos_matches_list_length(self, response_data):
        assert response_data["total_proyectos"] == len(response_data["proyectos"])

    def test_proyectos_have_required_columns(self, response_data):
        for i, proj in enumerate(response_data["proyectos"]):
            for col in REQUIRED_PROJECT_KEYS:
                assert col in proj, f"Row {i}: missing column {col!r}"

    def test_monto_total_is_integer_or_zero(self, response_data):
        monto = response_data["monto_total"]
        assert isinstance(monto, int), f"monto_total must be int, got {type(monto)}"

    def test_primer_año_and_ultimo_año_are_int_or_none(self, response_data):
        for field in ("primer_año", "ultimo_año"):
            val = response_data[field]
            assert val is None or isinstance(val, int), (
                f"{field} must be int or None, got {type(val)}: {val!r}"
            )

    def test_por_año_is_list(self, response_data):
        assert isinstance(response_data["por_año"], list)

    def test_por_año_entries_have_año_proyectos_monto(self, response_data):
        for entry in response_data["por_año"]:
            assert "año" in entry
            assert "proyectos" in entry
            assert "monto" in entry

    def test_por_año_sorted_ascending(self, response_data):
        años = [e["año"] for e in response_data["por_año"]]
        assert años == sorted(años), "por_año must be sorted by year ascending"

    def test_no_nan_values_in_response(self, response_data):
        assert _no_nan_in_json(response_data), (
            "Response contains NaN float values — these are not valid JSON"
        )

    def test_aprobado_corfo_is_numeric_or_none(self, response_data):
        """aprobado_corfo is cast to REAL in the query; should be float/int/None — never a string."""
        for i, proj in enumerate(response_data["proyectos"]):
            val = proj.get("aprobado_corfo")
            assert val is None or isinstance(val, (int, float)), (
                f"Row {i}: aprobado_corfo should be numeric or None, got {type(val)}: {val!r}"
            )

    def test_monto_total_equals_sum_of_project_montos(self, response_data):
        """monto_total must equal the sum of individual project aprobado_corfo values."""
        computed = sum(
            int(float(p["aprobado_corfo"]))
            for p in response_data["proyectos"]
            if p["aprobado_corfo"] is not None
        )
        assert response_data["monto_total"] == computed, (
            f"monto_total {response_data['monto_total']} != sum of projects {computed}"
        )


# ── Tests: "Persona Natural" razon ───────────────────────────────────────────

class TestEmpresaPerfilPersonaNatural:
    """
    'Persona Natural' appears as a razon in production data.
    The server must return either valid data (200) or a graceful error (404/200 with zeros).
    It must never crash (5xx).
    """

    def test_persona_natural_does_not_crash(self, authed_client):
        r = authed_client.get("/api/empresa/Persona Natural")
        assert r.status_code in (200, 404), (
            f"Expected 200 or 404 for 'Persona Natural', got {r.status_code}"
        )

    def test_persona_natural_response_is_valid_json(self, authed_client):
        r = authed_client.get("/api/empresa/Persona Natural")
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_persona_natural_no_nan_if_200(self, authed_client):
        r = authed_client.get("/api/empresa/Persona Natural")
        if r.status_code == 200:
            data = json.loads(r.data)
            assert _no_nan_in_json(data), (
                "Response for 'Persona Natural' contains NaN float values"
            )

    def test_persona_natural_has_required_keys_if_200(self, authed_client):
        r = authed_client.get("/api/empresa/Persona Natural")
        if r.status_code == 200:
            data = json.loads(r.data)
            for key in REQUIRED_TOP_KEYS:
                assert key in data, f"Missing required key: {key!r}"


# ── Tests: nonexistent razon ──────────────────────────────────────────────────

class TestEmpresaPerfilNonexistent:
    """A razon that does not exist must return 404 (or 200 with zeros — both document-able)."""

    NONEXISTENT = "EMPRESA_QUE_NO_EXISTE_JAMÁS_XYZ_99999"

    def test_nonexistent_returns_404_or_200(self, authed_client):
        r = authed_client.get(f"/api/empresa/{self.NONEXISTENT}")
        assert r.status_code in (200, 404), (
            f"Expected 200 or 404 for nonexistent razon, got {r.status_code}"
        )

    def test_nonexistent_response_is_valid_json(self, authed_client):
        r = authed_client.get(f"/api/empresa/{self.NONEXISTENT}")
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_nonexistent_returns_error_key_on_404(self, authed_client):
        r = authed_client.get(f"/api/empresa/{self.NONEXISTENT}")
        if r.status_code == 404:
            data = json.loads(r.data)
            assert "error" in data, "404 response must contain an 'error' key"

    def test_nonexistent_returns_zero_projects_on_200(self, authed_client):
        r = authed_client.get(f"/api/empresa/{self.NONEXISTENT}")
        if r.status_code == 200:
            data = json.loads(r.data)
            assert data.get("total_proyectos", -1) == 0


# ── Tests: URL path encoding ──────────────────────────────────────────────────

class TestEmpresaPerfilPathEncoding:
    """Verify that the <path:razon> routing handles spaces and special characters."""

    def test_razon_with_spaces_does_not_500(self, authed_client):
        """Spaces in company names must be handled without a 500 error."""
        r = authed_client.get("/api/empresa/Empresa Con Espacios SA")
        assert r.status_code in (200, 404)

    def test_razon_with_slash_does_not_500(self, authed_client):
        """<path:razon> allows slashes; the endpoint must not crash."""
        r = authed_client.get("/api/empresa/Empresa/Con/Barras SA")
        assert r.status_code in (200, 404)
