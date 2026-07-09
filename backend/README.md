# Backend MVP

FastAPI realtime backend for the 1v1 English tutor agent.

## Run locally
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in `DEEPSEEK_API_KEY`
4. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## LLM provider (DeepSeek)
- Default `LLM_PROVIDER=deepseek`, OpenAI-compatible API: https://api-docs.deepseek.com/
- Set `DEEPSEEK_API_KEY` in `backend/.env` (see `.env.example`). Until a real key is set,
  replies fall back to a labeled placeholder (`[DeepSeek API key not configured] ...`)
  so the rest of the pipeline keeps working.
- Model defaults to `deepseek-v4-flash`; override with `DEEPSEEK_MODEL` if needed.

## ASR provider (Deepgram)
- Default `ASR_PROVIDER=deepgram`, prerecorded transcription API: https://developers.deepgram.com/docs/pre-recorded-audio
- Set `DEEPGRAM_API_KEY` in `backend/.env` (see `.env.example`). Until a real key is set,
  transcripts fall back to a labeled placeholder (`[Deepgram API key not configured] ...`)
  so the rest of the pipeline (LLM reply + TTS) keeps working.
- Model defaults to `nova-3`; override with `DEEPGRAM_MODEL` if needed.
- Only the final audio chunk (`audio.commit`) is sent to Deepgram — partial chunks
  are not transcribed remotely to avoid double-billing the same audio.

## ASR provider (Alibaba Cloud NLS, optional alternative)
- Set `ASR_PROVIDER=alibaba` to use Alibaba Cloud Intelligent Speech Interaction
  (一句话识别 / one-sentence recognition) instead of Deepgram.
- Requires three values from your Alibaba Cloud account:
  - `ALIBABA_APP_KEY`: create a project in the [Intelligent Speech Interaction console](https://nls-portal.console.aliyun.com/)
    to get an AppKey.
  - `ALIBABA_ACCESS_KEY_ID` / `ALIBABA_ACCESS_KEY_SECRET`: create a RAM AccessKey pair
    in the [RAM console](https://ram.console.aliyun.com/manage/ak). These are used to
    automatically fetch (and refresh) a short-lived `X-NLS-Token` — no manual token
    copy/paste needed.
- Until real credentials are set, transcripts fall back to a labeled placeholder
  (`[Alibaba Cloud NLS credentials not configured] ...`) so the rest of the pipeline
  keeps working.
- **Audio format constraint**: Alibaba's one-sentence recognition only accepts mono
  audio at 8000 Hz or 16000 Hz. The mobile app's `audioRecorder.ts` is configured to
  record 16000 Hz mono AAC (`.m4a`) so both Deepgram and Alibaba work without changes.
- Only the final audio chunk (`audio.commit`) is sent to Alibaba — same rationale as
  Deepgram (avoid double-billing/quota usage on partial chunks).

## TTS provider (Deepgram Aura-2)
- Default `TTS_PROVIDER=deepgram`, text-to-speech API: https://developers.deepgram.com/docs/text-to-speech
- Reuses `DEEPGRAM_API_KEY` from the ASR section above — same Deepgram account, no
  extra key needed. Until a real key is set, `agent.audio` carries placeholder bytes
  (`DEEPGRAM_TTS_PLACEHOLDER::...`) that the mobile client detects and skips playback
  for (falls back to on-device `expo-speech` instead — see `mobile/src/services/textToSpeech.ts`).
- Voice defaults to `aura-2-thalia-en`; override with `DEEPGRAM_TTS_MODEL` — browse
  voices at https://developers.deepgram.com/docs/tts-models.
- Requests raw 16-bit PCM with no container (`encoding=linear16&container=none`) at
  `DEEPGRAM_TTS_SAMPLE_RATE` (default `24000` Hz) so the bytes can be sent straight
  through `agent.audio` — the mobile client wraps them in a WAV header itself.
- `TTS_PROVIDER=elevenlabs` / `azure` remain available as unimplemented placeholders
  (return labeled fake bytes) for future real integrations.

## Dev auth token
- `POST /v1/auth/dev-token` returns a short-lived JWT for local websocket tests.

## Realtime endpoint
- `wss://<host>/v1/realtime/session`
- Requires `Authorization: Bearer <jwt>`.

## Tests
- `pip install -r requirements-dev.txt`
- `pytest` (run from `backend/`)
- Covers `/healthz`, `/v1/auth/dev-token`, the full `/v1/realtime/session` WebSocket
  flow (auth, `session.start`/`audio.chunk`/`audio.commit`/`session.input_text`/`session.stop`,
  unsupported events), and the pure `evaluation`/`lesson_planner` helpers.
- `tests/conftest.py` forces every provider API key to a placeholder value before the
  app is imported, so the suite never hits real DeepSeek/Deepgram/Alibaba APIs or
  depends on whatever is in your local `.env` — safe to run offline and in CI.
- Swagger UI (`/docs`) is for humans; for **automated** API contract testing, point a
  schema-driven tool (e.g. [schemathesis](https://schemathesis.readthedocs.io/)) at the
  live `/openapi.json` instead — `schemathesis run http://localhost:8000/openapi.json`.
