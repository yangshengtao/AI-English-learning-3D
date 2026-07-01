# Backend MVP

FastAPI realtime backend for the 1v1 English tutor agent.

## Run locally
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload --port 8000`

## Dev auth token
- `POST /v1/auth/dev-token` returns a short-lived JWT for local websocket tests.

## Realtime endpoint
- `wss://<host>/v1/realtime/session`
- Requires `Authorization: Bearer <jwt>`.
