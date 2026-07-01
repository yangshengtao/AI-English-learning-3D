# Realtime Protocol and Auth Spec

## Transport
- Protocol: WebSocket over TLS (`wss://`).
- Endpoint: `/v1/realtime/session`.
- Session mode: one learner + one tutor agent.

## Auth
- Client obtains short-lived JWT from backend REST endpoint.
- WebSocket handshake header: `Authorization: Bearer <jwt>`.
- JWT TTL: 30 minutes, renewable via refresh token API.
- Required claims:
  - `sub`: user id
  - `sid`: session id
  - `role`: learner
  - `exp`: expiry timestamp

## Message Envelope
All websocket frames use JSON:

```json
{
  "type": "message_type",
  "sessionId": "sess_123",
  "traceId": "trace_abc",
  "timestampMs": 1760000000000,
  "payload": {}
}
```

## Client -> Server Events
- `session.start`
  - payload: `{ "mode": "free_talk|scenario|shadowing", "scenario": "optional" }`
- `audio.chunk`
  - payload: `{ "seq": 12, "audioBase64": "...", "sampleRate": 16000, "format": "pcm16" }`
- `audio.commit`
  - payload: `{ "lastSeq": 42 }`
- `session.input_text`
  - payload: `{ "text": "hello teacher" }` (fallback when voice unavailable)
- `session.stop`
  - payload: `{}`

## Server -> Client Events
- `session.ack`
  - payload: `{ "providerRoute": { "asr": "deepgram", "tts": "elevenlabs" } }`
- `asr.partial`
  - payload: `{ "text": "I want to...", "confidence": 0.83 }`
- `asr.final`
  - payload: `{ "text": "I want to order coffee.", "confidence": 0.91 }`
- `agent.text`
  - payload: `{ "text": "Great. You can say: I'd like a coffee, please." }`
- `agent.audio`
  - payload: `{ "audioBase64": "...", "sampleRate": 24000, "format": "pcm16" }`
- `avatar.cue`
  - payload: `{ "visemeTimeline": [], "emotion": "encouraging" }`
- `eval.feedback`
  - payload: `{ "pronunciationScore": 0.72, "tips": ["Try softer R sound."] }`
- `error`
  - payload: `{ "code": "AUTH_EXPIRED|PROVIDER_TIMEOUT|INVALID_PAYLOAD", "message": "..." }`
- `session.end`
  - payload: `{ "durationSec": 600, "turnCount": 22 }`

## Reliability Rules
- Sequence check for `audio.chunk`:
  - if gap detected, server emits `error` with `INVALID_CHUNK_SEQUENCE`.
- Idempotency:
  - duplicated chunks with same `seq` are ignored.
- Timeout:
  - idle > 45s closes session with `session.end`.
- Reconnect:
  - client may reconnect within 15s using same `sid`.

## Security and Abuse Controls
- Max payload per frame: 128 KB.
- Max incoming frame rate: 50 frames/sec.
- Server-side input moderation on text and transcript.
- Per-user and per-IP rate limits at API gateway.
