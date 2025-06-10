from app import app, Session, User



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


def test_registration_and_login():
    client = app.test_client()
    # register new user
    resp = client.post('/register', data={'username': 'test', 'password': 'pass'}, follow_redirects=True)
    assert resp.status_code == 200
    # login with new user
    resp = client.post('/login', data={'username': 'test', 'password': 'pass'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Benvenuto test' in resp.data
    # clean up
    session = Session()
    user = session.query(User).filter_by(username='test').first()
    if user:
        session.delete(user)
        session.commit()
    session.close()
