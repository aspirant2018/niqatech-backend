import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch , MagicMock
from app.main import app  

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    """ Fixture to mock the database session. """
    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
    return mock_db_session

def test_google_auth_first_login(mock_db_session):
    """ Test Google authentication for a first-time user login. """
    fake_token = "fake-google-oauth-token"

    fake_id_info = {
        'sub': '1234567890',
        'email': 'test@example.com'
    }
    with patch('app.v1.routers.auth.id_token.verify_oauth2_token', return_value=fake_id_info), \
            patch('app.v1.routers.auth.get_db', return_value=mock_db_session):
    
            response = client.post("/auth/google", json={"token": fake_token})
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "User first login. Please complete the profile."
            assert data["user_id"] == '1234567890'
            assert data["email"] == 'test@example.com'
            assert "jwt_token" in data


def test_root_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}

def test_invalid_endpoint():
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404

