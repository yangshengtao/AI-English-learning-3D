from __future__ import annotations

import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.auth import AuthError, decode_jwt, parse_bearer_token
from app.config import settings
from app.models.events import EventEnvelope, OutboundEvent
from app.orchestrator.session_agent import SessionAgent
from app.providers.factory import build_asr_provider, build_llm_provider, build_tts_provider

app = FastAPI(title=settings.app_name)
session_agent = SessionAgent(
    asr=build_asr_provider(),
    tts=build_tts_provider(),
    llm=build_llm_provider(),
)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "env": settings.env}


@app.post("/v1/auth/dev-token")
async def dev_token(user_id: str = "demo-user") -> dict:
    # Dev-only helper for local smoke tests.
    import jwt

    now = int(time.time())
    claims = {"sub": user_id, "sid": f"sess-{user_id}", "role": "learner", "iat": now, "exp": now + 1800}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return {"token": token}


@app.websocket("/v1/realtime/session")
async def realtime_session(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        token = parse_bearer_token(websocket)
        _claims = decode_jwt(token)
    except AuthError as exc:
        await websocket.send_json(
            OutboundEvent(
                type="error",
                sessionId="unknown",
                traceId="auth",
                timestampMs=int(time.time() * 1000),
                payload={"code": "AUTH_FAILED", "message": str(exc)},
            ).model_dump(by_alias=True)
        )
        await websocket.close(code=4401)
        return

    try:
        while True:
            raw = await websocket.receive_json()
            event = EventEnvelope.model_validate(raw)
            responses = await session_agent.handle(event)
            for item in responses:
                await websocket.send_json(item.model_dump(by_alias=True))
    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - safety net
        await websocket.send_json(
            OutboundEvent(
                type="error",
                sessionId="unknown",
                traceId="internal",
                timestampMs=int(time.time() * 1000),
                payload={"code": "INTERNAL_ERROR", "message": str(exc)},
            ).model_dump(by_alias=True)
        )
        await websocket.close(code=1011)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": str(exc)})

