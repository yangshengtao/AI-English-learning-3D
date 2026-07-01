# MVP KPI and Cost Monitoring

## Product KPI (MVP Acceptance)
- Voice response latency:
  - P50 < 1.8s
  - P95 < 3.0s
- Session reliability:
  - 15-minute session success rate >= 98%
- ASR readability:
  - daily-scene English transcription accuracy >= 90%
- TTS quality:
  - MOS >= 4.0/5.0 from internal reviewers
- Learning impact:
  - at least 1 actionable pronunciation tip per completed turn

## Technical SLOs
- WebSocket connected session drop rate < 2%.
- Provider timeout rate < 1%.
- Backend error rate (`5xx`) < 0.5%.
- Mean reconnect recovery time < 15s.

## Cost Metrics (per Session)
- `asr_cost_usd`
- `tts_cost_usd`
- `llm_cost_usd`
- `total_cost_usd`
- `duration_sec`
- `cost_per_minute_usd`

## Cost Guardrails
- Soft monthly cap: $500 (alert at 70%, 90%).
- Hard monthly cap: $800 (automatic downgrade policy).
- Per-session cap: $0.20
  - when exceeded, switch to lower-cost provider route for remaining turns.

## Data Schema (suggested)
```sql
CREATE TABLE session_cost_metrics (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  asr_cost_usd NUMERIC(10, 5) NOT NULL DEFAULT 0,
  tts_cost_usd NUMERIC(10, 5) NOT NULL DEFAULT 0,
  llm_cost_usd NUMERIC(10, 5) NOT NULL DEFAULT 0,
  total_cost_usd NUMERIC(10, 5) NOT NULL DEFAULT 0,
  duration_sec INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Monitoring Stack
- Metrics: Prometheus counters and histograms.
- Dashboards: Grafana boards for latency, provider error, and cost.
- Error tracking: Sentry for backend exceptions and mobile crash data.
- Alerts:
  - latency breach (P95 > 3.0s over 10 min)
  - provider failure burst (> 5% in 5 min)
  - cost spike (daily burn > expected by 30%)
