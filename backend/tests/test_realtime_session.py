from __future__ import annotations

import time

import jwt
from fastapi.testclient import TestClient

from app.config import settings


def _make_token(user_id: str = "ws-tester") -> str:
    now = int(time.time())
    claims = {
        "sub": user_id,
        "sid": f"sess-{user_id}",
        "role": "learner",
        "iat": now,
        "exp": now + 1800,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _envelope(event_type: str, *, session_id: str, trace_id: str, payload: dict) -> dict:
    return {
        "type": event_type,
        "sessionId": session_id,
        "traceId": trace_id,
        "timestampMs": int(time.time() * 1000),
        "payload": payload,
    }


def test_rejects_connection_without_token(client: TestClient) -> None:
    with client.websocket_connect("/v1/realtime/session") as ws:
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["payload"]["code"] == "AUTH_FAILED"


def test_rejects_connection_with_invalid_token(client: TestClient) -> None:
    with client.websocket_connect("/v1/realtime/session?token=not-a-real-jwt") as ws:
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["payload"]["code"] == "AUTH_FAILED"


def test_session_start_ack_reports_configured_providers(client: TestClient) -> None:
    token = _make_token()
    session_id = "sess-ws-tester"
    with client.websocket_connect(f"/v1/realtime/session?token={token}") as ws:
        ws.send_json(_envelope("session.start", session_id=session_id, trace_id="t1", payload={"mode": "free_talk"}))
        ack = ws.receive_json()

        assert ack["type"] == "session.ack"
        assert ack["payload"]["providerRoute"] == {
            "asr": settings.asr_provider,
            "tts": settings.tts_provider,
            "llm": settings.llm_provider,
        }


def test_text_turn_returns_placeholder_agent_reply(client: TestClient) -> None:
    token = _make_token(user_id="ws-tester-text")
    session_id = "sess-ws-tester-text"
    with client.websocket_connect(f"/v1/realtime/session?token={token}") as ws:
        ws.send_json(_envelope("session.start", session_id=session_id, trace_id="t1", payload={"mode": "free_talk"}))
        ws.receive_json()  # session.ack

        ws.send_json(
            _envelope("session.input_text", session_id=session_id, trace_id="t2", payload={"text": "Hello there"})
        )
        reply = ws.receive_json()

        assert reply["type"] == "agent.text"
        assert "DeepSeek API key not configured" in reply["payload"]["text"]
        assert "Hello there" in reply["payload"]["text"]


def test_audio_turn_runs_full_pipeline(client: TestClient) -> None:
    token = _make_token(user_id="ws-tester-audio")
    session_id = "sess-ws-tester-audio"
    with client.websocket_connect(f"/v1/realtime/session?token={token}") as ws:
        ws.send_json(_envelope("session.start", session_id=session_id, trace_id="t1", payload={"mode": "free_talk"}))
        ws.receive_json()  # session.ack

        ws.send_json(
            _envelope(
                "audio.chunk",
                session_id=session_id,
                trace_id="t2",
                payload={"audioBase64": "ZmFrZS1hdWRpby1ieXRlcw==", "format": "wav"},
            )
        )
        partial = ws.receive_json()
        assert partial["type"] == "asr.partial"

        ws.send_json(_envelope("audio.commit", session_id=session_id, trace_id="t3", payload={}))

        final = ws.receive_json()
        assert final["type"] == "asr.final"
        assert "Deepgram API key not configured" in final["payload"]["text"]

        agent_text = ws.receive_json()
        assert agent_text["type"] == "agent.text"

        agent_audio = ws.receive_json()
        assert agent_audio["type"] == "agent.audio"
        assert agent_audio["payload"]["format"] == "pcm16"

        avatar_cue = ws.receive_json()
        assert avatar_cue["type"] == "avatar.cue"

        eval_feedback = ws.receive_json()
        assert eval_feedback["type"] == "eval.feedback"


def test_unsupported_event_type_returns_error(client: TestClient) -> None:
    token = _make_token(user_id="ws-tester-unsupported")
    session_id = "sess-ws-tester-unsupported"
    with client.websocket_connect(f"/v1/realtime/session?token={token}") as ws:
        ws.send_json(_envelope("totally.unknown", session_id=session_id, trace_id="t1", payload={}))
        message = ws.receive_json()

        assert message["type"] == "error"
        assert message["payload"]["code"] == "UNSUPPORTED_EVENT"


def test_session_stop_reports_turn_count(client: TestClient) -> None:
    token = _make_token(user_id="ws-tester-stop")
    session_id = "sess-ws-tester-stop"
    with client.websocket_connect(f"/v1/realtime/session?token={token}") as ws:
        ws.send_json(_envelope("session.start", session_id=session_id, trace_id="t1", payload={"mode": "free_talk"}))
        ws.receive_json()  # session.ack

        ws.send_json(
            _envelope("session.input_text", session_id=session_id, trace_id="t2", payload={"text": "One turn"})
        )
        ws.receive_json()  # agent.text

        ws.send_json(_envelope("session.stop", session_id=session_id, trace_id="t3", payload={}))
        end = ws.receive_json()

        assert end["type"] == "session.end"
        # session.input_text does not append to history (only audio.commit does),
        # so the turn count stays at 0 for a text-only session.
        assert end["payload"]["turnCount"] == 0
