"""
tests/conftest.py
-----------------
Fixtures compartidas para la suite de pruebas del CORFO Analytics Platform.

El fixture principal `seed_db` crea una base de datos SQLite en memoria,
ejecuta tests/seed_data.sql contra ella y la entrega lista para consultar.
No requiere acceso a corfo_alimentos.db ni a ningún recurso externo.

El fixture `authed_client` provee un cliente Flask con sesión de login activa,
necesario para endpoints protegidos con @login_required.
"""

import sqlite3
import os
import sys
import pytest

# Set required env vars before any project module is imported.
# DATAINNOVACION_TOKEN is validated at module-level in sync/datainnovacion_sync.py,
# so it must be present before corfo_server (which imports that module) is loaded.
if not os.environ.get("DATAINNOVACION_TOKEN"):
    os.environ["DATAINNOVACION_TOKEN"] = "test-token-placeholder"

# Ensure project root is on path so corfo_server can be imported from any cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ruta absoluta al archivo SQL de semilla, relativa a este conftest
_SEED_SQL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.sql")


@pytest.fixture
def seed_db() -> sqlite3.Connection:
    """
    Fixture que provee una conexión SQLite en memoria poblada con el dataset semilla.

    Crea las tablas `proyectos` y `leads` con el mismo esquema que producción
    e inserta ~30 filas en proyectos y 3 en leads.

    Uso:
        def test_algo(seed_db):
            cur = seed_db.cursor()
            cur.execute('SELECT COUNT(*) FROM proyectos')
            total = cur.fetchone()[0]
            assert total == 30

    La conexión se cierra automáticamente al terminar el test.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row  # permite acceso por nombre de columna

    with open(_SEED_SQL_PATH, encoding="utf-8") as f:
        sql_script = f.read()

    conn.executescript(sql_script)
    conn.commit()

    yield conn

    conn.close()


@pytest.fixture(scope="module")
def app():
    """Flask app instance configured for testing."""
    from corfo_server import app as flask_app
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture(scope="module")
def authed_client(app):
    """Flask test client with an active login session."""
    from werkzeug.security import generate_password_hash
    # Use test credentials — override module-level vars so login works without a real .env
    test_username = "test_admin"
    test_password = "test_password_123"

    import corfo_server
    corfo_server._ADMIN_USERNAME = test_username
    corfo_server._ADMIN_PASSWORD_HASH = generate_password_hash(test_password)

    with app.test_client() as client:
        client.post(
            "/api/auth/login",
            json={"username": test_username, "password": test_password}
        )
        yield client
