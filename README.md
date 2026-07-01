# AI English Learning 3D (MVP Scaffold)

This repository now contains an implementation scaffold for a 1v1 digital-human English tutor:
- backend orchestration and realtime websocket API
- mobile React Native session modules
- infrastructure manifests
- product/engineering planning docs

## Repository Layout
- `backend/`: FastAPI realtime backend with provider abstraction.
- `mobile/`: RN screen/services/components for session interaction.
- `infra/`: local docker compose and Kubernetes deployment baseline.
- `docs/`: vendor shortlist, realtime protocol, KPI and cost strategy.

## Quick Start
### Backend
1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload --port 8000`

### Local Infra
1. `cd infra`
2. `docker compose up`

## Suggested Skills/Agents for Next Phase
- Optional now, useful when team scale grows:
  - CI babysit automation skill for PR/CI loops
  - end-to-end delivery workflow skill for docs and release automation
  - security scanning and regression execution agents in pre-release pipeline

## Current Status
- This is an implementation baseline for MVP architecture.
- Provider SDK integrations are intentionally placeholder-first and ready for real API wiring.
