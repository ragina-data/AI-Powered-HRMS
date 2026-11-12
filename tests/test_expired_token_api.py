from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_expired_token_is_rejected():
    expired_token, _ = create_access_token(
    user_id=1,
    session_id=1,
    expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Could not validate authentication credentials"
    )