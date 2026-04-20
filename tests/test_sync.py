"""
tests/test_sync.py
-------------------
Unit tests for sync/datainnovacion_sync.py.
Mocks the datainnovacion.cl API — no internet required.

Run: python -m pytest tests/test_sync.py -v
"""

import json
import sqlite3
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.datainnovacion_sync import (
    transform,
    upsert_proyectos,
    ensure_sync_log_table,
    ensure_proyectos_pk_column,
    run_sync,
    COLUMN_MAP,
    PRIMARY_KEY_DB,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_API_RESPONSE = [
    {
        # API field names must match COLUMN_MAP keys in sync/datainnovacion_sync.py
        "id": "PROY-001",                          # → codigo
        "razon_social": "Empresa Alimentos SA",    # → razon
        "monto_aprobado": "50000000",              # → aprobado_corfo (TEXT)
        "anio_adjudicacion": 2022,                 # → año_adjudicacion (INTEGER)
        "region": "Región Metropolitana",          # → region_ejecucion
        "sector": "Alimentos",                     # → sector_economico
        "tipo_innovacion": "Proceso",              # → tipo_innovacion
        "tipo_proyecto": "I+D Aplicada",           # → tipo_proyecto
        "tendencia": "Biotecnología",              # → tendencia_final
        "sostenible": "Sí",                        # → sostenible
        "economia_circular": "No",                 # → economia_circular_si_no
    },
    {
        "id": "PROY-002",
        "razon_social": "Tech Startup Ltda",
        "monto_aprobado": "120000000",
        "anio_adjudicacion": 2023,
        "region": "Región de Valparaíso",
        "sector": "TI",
        "tipo_innovacion": "Producto",
        "tipo_proyecto": "Innova",
        "tendencia": "Inteligencia Artificial",
        "sostenible": "No",
        "economia_circular": "Sí",
    },
]


@pytest.fixture
def tmp_db():
    """Create a temporary SQLite DB with the proyectos table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE proyectos (
            razon TEXT,
            aprobado_corfo TEXT,
            "año_adjudicacion" INTEGER,
            region_ejecucion TEXT,
            sector_economico TEXT,
            tipo_innovacion TEXT,
            tipo_proyecto TEXT,
            tendencia_final TEXT,
            sostenible TEXT,
            economia_circular_si_no TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY,
            razon TEXT,
            monto_total_aprobado REAL
        )
    """)
    conn.execute("INSERT INTO leads (razon, monto_total_aprobado) VALUES ('Empresa CRM', 999)")
    conn.commit()
    conn.close()

    yield db_path
    os.unlink(db_path)


# ── transform() ───────────────────────────────────────────────────────────────

class TestTransform:
    def test_renames_columns(self):
        df = pd.DataFrame(MOCK_API_RESPONSE)
        result = transform(df)
        assert "razon" in result.columns
        assert "aprobado_corfo" in result.columns
        assert "año_adjudicacion" in result.columns

    def test_aprobado_corfo_stays_text(self):
        df = pd.DataFrame(MOCK_API_RESPONSE)
        result = transform(df)
        assert result["aprobado_corfo"].dtype == object  # TEXT in pandas

    def test_año_adjudicacion_is_integer(self):
        df = pd.DataFrame(MOCK_API_RESPONSE)
        result = transform(df)
        assert pd.api.types.is_integer_dtype(result["año_adjudicacion"])

    def test_handles_missing_columns_gracefully(self):
        """If API drops a column, transform should log warning and continue."""
        partial = [{"id": "X", "razon_social": "Test"}]
        df = pd.DataFrame(partial)
        result = transform(df)
        assert "razon" in result.columns

    def test_row_count_preserved(self):
        df = pd.DataFrame(MOCK_API_RESPONSE)
        result = transform(df)
        assert len(result) == len(MOCK_API_RESPONSE)


# ── upsert_proyectos() ────────────────────────────────────────────────────────

class TestUpsert:
    def test_inserts_rows(self, tmp_db):
        df = pd.DataFrame(MOCK_API_RESPONSE)
        df = transform(df)
        conn = sqlite3.connect(tmp_db)
        ensure_proyectos_pk_column(conn)
        count = upsert_proyectos(conn, df)
        conn.close()
        assert count == len(MOCK_API_RESPONSE)

    def test_does_not_touch_leads(self, tmp_db):
        """The leads table must be unchanged after sync."""
        df = pd.DataFrame(MOCK_API_RESPONSE)
        df = transform(df)
        conn = sqlite3.connect(tmp_db)
        ensure_proyectos_pk_column(conn)
        upsert_proyectos(conn, df)
        leads = conn.execute("SELECT * FROM leads").fetchall()
        conn.close()
        assert len(leads) == 1
        assert leads[0][1] == "Empresa CRM"

    def test_upsert_is_idempotent(self, tmp_db):
        """Running upsert twice with the same data should not duplicate rows."""
        df = pd.DataFrame(MOCK_API_RESPONSE)
        df = transform(df)
        conn = sqlite3.connect(tmp_db)
        ensure_proyectos_pk_column(conn)
        upsert_proyectos(conn, df)
        upsert_proyectos(conn, df)
        count = conn.execute("SELECT COUNT(*) FROM proyectos").fetchone()[0]
        conn.close()
        assert count == len(MOCK_API_RESPONSE)  # not doubled


# ── run_sync() ────────────────────────────────────────────────────────────────

class TestRunSync:
    def _mock_response(self):
        mock = MagicMock()
        mock.raise_for_status.return_value = None
        mock.json.return_value = MOCK_API_RESPONSE
        return mock

    def test_successful_sync(self, tmp_db):
        with patch("sync.datainnovacion_sync.requests.get", return_value=self._mock_response()):
            with patch("sync.datainnovacion_sync.DB_PATH", tmp_db):
                result = run_sync()

        assert result["status"] == "ok"
        assert result["rows_fetched"] == len(MOCK_API_RESPONSE)
        assert result["rows_upserted"] == len(MOCK_API_RESPONSE)

    def test_sync_logs_to_sync_log_table(self, tmp_db):
        with patch("sync.datainnovacion_sync.requests.get", return_value=self._mock_response()):
            with patch("sync.datainnovacion_sync.DB_PATH", tmp_db):
                run_sync()

        conn = sqlite3.connect(tmp_db)
        log_rows = conn.execute("SELECT * FROM _sync_log").fetchall()
        conn.close()
        assert len(log_rows) == 1
        assert log_rows[0][5] == "ok"  # status column

    def test_api_failure_returns_error(self, tmp_db):
        import requests as req
        with patch("sync.datainnovacion_sync.requests.get", side_effect=req.RequestException("timeout")):
            with patch("sync.datainnovacion_sync.DB_PATH", tmp_db):
                result = run_sync()

        assert result["status"] == "error"
        assert "error_message" in result

    def test_api_failure_logs_error_status(self, tmp_db):
        import requests as req
        with patch("sync.datainnovacion_sync.requests.get", side_effect=req.RequestException("timeout")):
            with patch("sync.datainnovacion_sync.DB_PATH", tmp_db):
                run_sync()

        conn = sqlite3.connect(tmp_db)
        log_rows = conn.execute("SELECT status, error_message FROM _sync_log").fetchall()
        conn.close()
        assert log_rows[0][0] == "error"
        assert "timeout" in log_rows[0][1]

    def test_sync_never_modifies_leads(self, tmp_db):
        """Critical: sync must never touch the leads table."""
        with patch("sync.datainnovacion_sync.requests.get", return_value=self._mock_response()):
            with patch("sync.datainnovacion_sync.DB_PATH", tmp_db):
                run_sync()

        conn = sqlite3.connect(tmp_db)
        leads = conn.execute("SELECT * FROM leads").fetchall()
        conn.close()
        assert len(leads) == 1
        assert leads[0][1] == "Empresa CRM"
