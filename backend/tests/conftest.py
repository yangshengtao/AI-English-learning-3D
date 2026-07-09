from __future__ import annotations

import os

# Force every external provider into placeholder mode *before* app.config is
# imported anywhere, so the suite never makes real network calls regardless
# of whatever real keys are sitting in backend/.env on this machine.
os.environ["DEEPSEEK_API_KEY"] = "REPLACE_WITH_DEEPSEEK_API_KEY"
os.environ["DEEPGRAM_API_KEY"] = "REPLACE_WITH_DEEPGRAM_API_KEY"
os.environ["ALIBABA_ACCESS_KEY_ID"] = "REPLACE_WITH_ALIBABA_ACCESS_KEY_ID"
os.environ["ALIBABA_ACCESS_KEY_SECRET"] = "REPLACE_WITH_ALIBABA_ACCESS_KEY_SECRET"
os.environ["ALIBABA_APP_KEY"] = "REPLACE_WITH_ALIBABA_APP_KEY"
os.environ["ASR_PROVIDER"] = "deepgram"
os.environ["TTS_PROVIDER"] = "elevenlabs"
os.environ["LLM_PROVIDER"] = "deepseek"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-bytes-long-for-hs256"
os.environ["ENV"] = "dev"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
