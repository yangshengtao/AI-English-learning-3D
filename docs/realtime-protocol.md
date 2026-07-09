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
  - **Mobile client note**: the current mobile app records one clip per turn with
    `expo-av` (`Audio.RecordingOptionsPresets.HIGH_QUALITY`) and uploads it as a
    single chunk with `format: "m4a"` (AAC), not `pcm16`. The server buffers the
    chunk's `audioBase64`/`format` on the session and only sends it to the ASR
    provider once `audio.commit` arrives (see below), so `pcm16` streaming chunks
    remain supported for future real-time streaming clients.
- `audio.commit`
  - payload: `{ "lastSeq": 42 }`
  - Server transcribes the most recently buffered `audio.chunk` payload using
    whichever ASR provider is configured (`ASR_PROVIDER=deepgram` or `alibaba`;
    real transcription when credentials are configured, otherwise a labeled
    placeholder transcript) and proceeds with the LLM reply.
  - Alibaba Cloud NLS (`alibaba`) only accepts mono audio at 8000/16000 Hz — the
    mobile client records 16000 Hz mono `.m4a` so it works with either provider.
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
  - payload: `{ "audioBase64": "...", "sampleRate": 24000, "format": "mp3" }`
  - `format` reflects the active TTS provider's `audio_format` (see
    `backend/app/providers/base.py`) — `"pcm16"` is raw PCM the client must
    wrap in a WAV header before playback; anything else (`"mp3"`, `"opus"`,
    ...) is a self-describing container the client can hand straight to its
    audio player. Deepgram Aura-2 defaults to `mp3` (see
    `DEEPGRAM_TTS_ENCODING`) since it's ~8x smaller over the wire than raw
    PCM for the same speech — see the "Stop Recording 到播放延迟高" entry in
    `docs/troubleshooting.md` for why that matters.
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
