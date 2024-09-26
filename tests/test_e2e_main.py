from fastapi import status
from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    response = client.get('api/healthchecker')

    assert response.status_code == status.HTTP_200_OK, response.text

    data = response.json()

    assert 'message' in data
    assert data['message'] == 'Welcome to FastAPI!'
