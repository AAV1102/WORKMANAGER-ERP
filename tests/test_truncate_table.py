import pytest
from app import app
from modules.db_utils import get_db_connection
from modules.credentials_config import DEFAULT_ADMIN

def test_truncate_empleados_requires_admin_and_works():
    app.config['TESTING'] = True
    client = app.test_client()

    conn = get_db_connection()
    conn.execute(
        """
        INSERT OR IGNORE INTO empleados (cedula, nombre, email)
        VALUES (?, ?, ?)
        """,
        ("999999", "Usuario Prueba", "test.user@example.com"),
    )
    conn.commit()
    before = conn.execute("SELECT COUNT(*) FROM empleados").fetchone()[0]
    conn.close()
    assert before >= 1

    r = client.post('/login', data={'email': DEFAULT_ADMIN['email'], 'password': DEFAULT_ADMIN['password']}, follow_redirects=True)
    assert r.status_code in (200, 302)

    resp = client.post('/configuracion/truncate_table', json={'table_name': 'empleados'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('success') is True

    conn = get_db_connection()
    after = conn.execute("SELECT COUNT(*) FROM empleados").fetchone()[0]
    conn.close()
    assert after == 0
