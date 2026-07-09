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

## Dev auth token
- `POST /v1/auth/dev-token` returns a short-lived JWT for local websocket tests.

## Realtime endpoint
- `wss://<host>/v1/realtime/session`
- Requires `Authorization: Bearer <jwt>`.
