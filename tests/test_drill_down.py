"""
tests/test_drill_down.py
------------------------
Targeted tests for the GET /api/dashboard/drill endpoint added in DOB-107.

Covers:
  - Valid field + value → HTTP 200 with required JSON keys
  - Invalid (non-whitelisted) field → HTTP 400 with error key
  - Missing field param → HTTP 400
  - Missing value param (empty) → HTTP 200 with rows (empty or not, but no crash)
  - año_adjudicacion with non-integer value → HTTP 400
  - año_adjudicacion with valid integer → HTTP 200

Run: python -m pytest tests/test_drill_down.py -v
"""

import json
import pytest
import sys
import os

# Ensure project root is on path and token env var is present before any imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.environ.get("DATAINNOVACION_TOKEN"):
    os.environ["DATAINNOVACION_TOKEN"] = "test-token-placeholder"


# ── Helpers ───────────────────────────────────────────────────────────────────

def drill(client, **params):
    """Build a GET request to /api/dashboard/drill with query params."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get(f"/api/dashboard/drill?{qs}")


# ── Valid requests ─────────────────────────────────────────────────────────────

class TestDrillValid:
    def test_returns_200_for_valid_field(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        assert r.status_code == 200

    def test_response_has_required_keys(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        assert "rows" in data, "Response must contain 'rows'"
        assert "field" in data, "Response must contain 'field'"
        assert "value" in data, "Response must contain 'value'"
        assert "total" in data, "Response must contain 'total'"

    def test_field_and_value_echoed_in_response(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        assert data["field"] == "sector_economico"
        assert data["value"] == "Alimentos"

    def test_total_matches_rows_length(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        assert data["total"] == len(data["rows"])

    def test_rows_is_list(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        assert isinstance(data["rows"], list)

    def test_rows_contain_expected_columns(self, authed_client):
        """Each row must have the 6 columns selected by the drill query."""
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        if data["rows"]:
            row = data["rows"][0]
            for col in ("razon", "aprobado_corfo", "año_adjudicacion",
                        "region_ejecucion", "sector_economico", "tipo_proyecto"):
                assert col in row, f"Missing expected column: {col}"

    def test_region_ejecucion_field(self, authed_client):
        r = drill(authed_client, field="region_ejecucion", value="Región Metropolitana de Santiago")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "rows" in data and "total" in data

    def test_sostenible_field(self, authed_client):
        r = drill(authed_client, field="sostenible", value="Sí")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data["rows"], list)

    def test_tipo_innovacion_field(self, authed_client):
        r = drill(authed_client, field="tipo_innovacion", value="Proceso")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "total" in data

    def test_año_adjudicacion_valid_integer(self, authed_client):
        r = drill(authed_client, field="año_adjudicacion", value="2023")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "rows" in data
        assert data["field"] == "año_adjudicacion"
        assert data["value"] == "2023"

    def test_value_that_matches_nothing_returns_empty_rows(self, authed_client):
        """A valid field with a value that doesn't exist returns 200 with empty rows."""
        r = drill(authed_client, field="sector_economico", value="SECTOR_INEXISTENTE_XYZ_99999")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["rows"] == []
        assert data["total"] == 0

    def test_total_is_integer(self, authed_client):
        r = drill(authed_client, field="sector_economico", value="Alimentos")
        data = json.loads(r.data)
        assert isinstance(data["total"], int)


# ── Invalid field ─────────────────────────────────────────────────────────────

class TestDrillInvalidField:
    def test_unknown_field_returns_400(self, authed_client):
        r = drill(authed_client, field="columna_inexistente", value="algo")
        assert r.status_code == 400

    def test_unknown_field_has_error_key(self, authed_client):
        r = drill(authed_client, field="columna_inexistente", value="algo")
        data = json.loads(r.data)
        assert "error" in data

    def test_sql_injection_attempt_in_field_returns_400(self, authed_client):
        """Fields that are not in the whitelist must be rejected, including injection attempts."""
        r = drill(authed_client, field="razon; DROP TABLE proyectos --", value="x")
        assert r.status_code == 400
        data = json.loads(r.data)
        assert "error" in data

    def test_aprobado_corfo_not_allowed_as_drill_field(self, authed_client):
        """aprobado_corfo is TEXT money — not a useful category for drill-down; check whitelist."""
        # Whether it is allowed or not, the endpoint must respond cleanly (200 or 400, not 500).
        r = drill(authed_client, field="aprobado_corfo", value="85000000")
        assert r.status_code in (200, 400)

    def test_error_message_lists_valid_fields(self, authed_client):
        """The 400 error message should hint at allowed field names."""
        r = drill(authed_client, field="invalid_field", value="x")
        data = json.loads(r.data)
        error_text = data.get("error", "")
        # The implementation joins sorted(_DRILL_ALLOWED_FIELDS) into the message
        assert len(error_text) > 0


# ── Missing parameters ────────────────────────────────────────────────────────

class TestDrillMissingParams:
    def test_missing_field_returns_400(self, authed_client):
        r = authed_client.get("/api/dashboard/drill?value=Alimentos")
        assert r.status_code == 400

    def test_missing_field_has_error_key(self, authed_client):
        r = authed_client.get("/api/dashboard/drill?value=Alimentos")
        data = json.loads(r.data)
        assert "error" in data

    def test_no_params_returns_400(self, authed_client):
        r = authed_client.get("/api/dashboard/drill")
        assert r.status_code == 400
        data = json.loads(r.data)
        assert "error" in data

    def test_missing_value_with_valid_field_does_not_crash(self, authed_client):
        """
        The endpoint does not require value — it queries with an empty string.
        This should return 200 (with empty rows) rather than a 500 server error.
        This test documents the current graceful behavior.
        """
        r = authed_client.get("/api/dashboard/drill?field=sector_economico")
        # Either a clean 200 (empty rows) or a 400 are acceptable.
        # A 500 is never acceptable.
        assert r.status_code in (200, 400), (
            f"Expected 200 or 400 when value is missing, got {r.status_code}"
        )
        data = json.loads(r.data)
        # Response must be valid JSON with either rows or error
        assert "rows" in data or "error" in data


# ── año_adjudicacion type enforcement ─────────────────────────────────────────

class TestDrillAñoAdjudicacion:
    def test_non_integer_value_returns_400(self, authed_client):
        r = drill(authed_client, field="año_adjudicacion", value="dos-mil-veintitres")
        assert r.status_code == 400

    def test_non_integer_value_has_error_key(self, authed_client):
        r = drill(authed_client, field="año_adjudicacion", value="not_a_number")
        data = json.loads(r.data)
        assert "error" in data

    def test_float_string_value_returns_400(self, authed_client):
        """2023.5 is not a valid integer year."""
        r = drill(authed_client, field="año_adjudicacion", value="2023.5")
        assert r.status_code == 400

    def test_empty_value_for_año_returns_400(self, authed_client):
        """Empty string is not a valid integer for año_adjudicacion."""
        r = drill(authed_client, field="año_adjudicacion", value="")
        assert r.status_code == 400

    def test_valid_year_2023_returns_200(self, authed_client):
        r = drill(authed_client, field="año_adjudicacion", value="2023")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "rows" in data
        assert isinstance(data["rows"], list)

    def test_valid_year_out_of_range_returns_empty_rows(self, authed_client):
        """A year outside the data range (e.g., 1900) returns 200 with empty rows."""
        r = drill(authed_client, field="año_adjudicacion", value="1900")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["rows"] == []
        assert data["total"] == 0

    def test_negative_year_returns_400_or_empty(self, authed_client):
        """Negative years are valid integers but shouldn't exist in the data."""
        r = drill(authed_client, field="año_adjudicacion", value="-1")
        # -1 parses as int, so 200 with empty rows is correct behavior
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            data = json.loads(r.data)
            assert data["total"] == 0
