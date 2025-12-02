import pytest
from app import app

def test_health():
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json()['status'] == 'ok'

def test_routes_endpoint():
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.get('/routes')
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert any(x['endpoint'] == 'index' for x in data)

def test_metrics():
    app.config['TESTING'] = True
    client = app.test_client()
    r = client.get('/metrics')
    assert r.status_code == 200
    assert isinstance(r.get_json(), dict)