from app import app

def test_index():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200


def test_login_page():
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200


def test_welcome_page():
    client = app.test_client()
    response = client.get('/welcome')
    assert response.status_code == 200
