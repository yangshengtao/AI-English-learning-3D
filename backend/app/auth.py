from __future__ import annotations

from typing import Any

import jwt
from fastapi import WebSocket

from app.config import settings


class AuthError(Exception):
    pass


def parse_bearer_token(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()

    query_token = websocket.query_params.get("token", "").strip()
    if query_token:
        return query_token

    raise AuthError("Missing bearer token.")


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired token.") from exc

