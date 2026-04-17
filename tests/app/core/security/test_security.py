from http import HTTPStatus

from jwt import decode

from app.core.security import create_access_token
from app.core.settings import Settings


def test_jwt():
    data = {'test': 'test'}

    token = create_access_token(data)

    decoded = decode(token, Settings().SECRET_KEY, algorithms=Settings().ALGORITHM)

    assert decoded['test'] == 'test'
    assert 'exp' in decoded


def test_jwt_invalid_token(client):
    response = client.get('/trainers/1', headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_get_current_user_not_found(client):
    data = {'no-email': 'no-email'}
    token = create_access_token(data)

    response = client.get('/trainers/1', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_get_current_user_does_not_exists(client):
    data = {'sub': 'test@test.com'}
    token = create_access_token(data)

    response = client.get('/trainers/1', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
