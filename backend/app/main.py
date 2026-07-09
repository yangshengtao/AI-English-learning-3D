from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from app.auth import AuthError, decode_jwt, parse_bearer_token
from app.config import settings
from app.models.events import EventEnvelope, OutboundEvent
from app.orchestrator.session_agent import SessionAgent
from app.providers.factory import build_asr_provider, build_llm_provider, build_tts_provider

# Use bootcdn (accessible in China) instead of jsdelivr for Swagger UI assets
SWAGGER_JS_URL = "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.js"
SWAGGER_CSS_URL = "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui.css"

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name, docs_url=None)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url=SWAGGER_JS_URL,
        swagger_css_url=SWAGGER_CSS_URL,
    )
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

    async def emit(item: OutboundEvent) -> None:
        await websocket.send_json(item.model_dump(by_alias=True))

    try:
        while True:
            raw = await websocket.receive_json()
            event = EventEnvelope.model_validate(raw)
            await session_agent.handle(event, emit)
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

