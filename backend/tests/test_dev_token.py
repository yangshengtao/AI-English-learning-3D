from __future__ import annotations

import jwt
from fastapi.testclient import TestClient

from app.config import settings


def test_dev_token_defaults_to_demo_user(client: TestClient) -> None:
    response = client.post("/v1/auth/dev-token")

    assert response.status_code == 200
    token = response.json()["token"]
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert claims["sub"] == "demo-user"
    assert claims["role"] == "learner"
    assert claims["exp"] > claims["iat"]


def test_dev_token_honors_custom_user_id(client: TestClient) -> None:
    response = client.post("/v1/auth/dev-token", params={"user_id": "alice"})

    assert response.status_code == 200
    token = response.json()["token"]
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert claims["sub"] == "alice"
    assert claims["sid"] == "sess-alice"
