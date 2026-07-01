from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    type: str
    session_id: str = Field(alias="sessionId")
    trace_id: str = Field(alias="traceId")
    timestamp_ms: int = Field(alias="timestampMs")
    payload: dict[str, Any] = Field(default_factory=dict)


class OutboundEvent(BaseModel):
    type: str
    session_id: str = Field(alias="sessionId")
    trace_id: str = Field(alias="traceId")
    timestamp_ms: int = Field(alias="timestampMs")
    payload: dict[str, Any] = Field(default_factory=dict)

