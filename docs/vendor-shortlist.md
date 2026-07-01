# Vendor Shortlist for MVP

## Scope
- Objective: pick primary and backup providers for ASR, TTS, and avatar streaming for a 1v1 English tutoring MVP.
- Constraints: prioritize fast delivery, stable realtime APIs, and balanced quality/cost.

## Recommended Provider Matrix
| Capability | Primary | Backup | Why |
| --- | --- | --- | --- |
| ASR (streaming) | Deepgram Nova-3 | Google Cloud Speech-to-Text V2 | Deepgram has low-latency websocket flow and strong English realtime transcripts; GCP is mature and globally stable. |
| TTS (American accent) | ElevenLabs Multilingual v2 | Azure Neural TTS | ElevenLabs has natural US voices; Azure provides strong enterprise fallback and broad region support. |
| Avatar streaming | HeyGen Streaming Avatar | D-ID / custom Web avatar page | HeyGen speeds up MVP for talking-head digital humans; backup protects against vendor outages and price shifts. |
| LLM Orchestration | OpenAI realtime/text model family | Anthropic or gateway-routed open models | Keeps quality high while preserving future provider routing flexibility. |

## Trial Account and Access Strategy
1. Create dedicated `mvp-dev` organization/projects per vendor.
2. Use separate API keys for `dev`, `staging`, and `prod`.
3. Store all secrets in backend env management only; never in mobile clients.
4. Enable hard budget caps and alert thresholds from day one.

## Vendor Readiness Checklist
- API latency baseline test (target: first token/audio under 800 ms in staging).
- Error semantics reviewed (retryable vs non-retryable).
- Region availability reviewed for target users.
- Billing dimensions verified (per minute, per character, per token).
- Fallback path tested by forced provider switch.

## Decision Lock for Phase 0
- ASR: primary `Deepgram`, backup `Google STT`.
- TTS: primary `ElevenLabs`, backup `Azure Neural TTS`.
- Avatar: primary `HeyGen Streaming`, backup `D-ID` or custom web avatar renderer.

## Account Setup Notes
- Use a shared team mailbox for vendor admin accounts.
- Turn on MFA for all provider consoles.
- Record API quotas and trial expiration dates in a project tracker.
