from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from app.config import settings
from app.models.events import EventEnvelope, OutboundEvent
from app.providers.base import ASRProvider, LLMProvider, TTSProvider
from app.services.evaluation import evaluate_pronunciation
from app.services.lesson_planner import choose_mode

logger = logging.getLogger(__name__)

Emit = Callable[[OutboundEvent], Awaitable[None]]


@dataclass
class SessionState:
    session_id: str
    mode: str = "free_talk"
    history: list[dict[str, str]] = field(default_factory=list)
    last_partial_text: str = ""
    pending_audio_base64: str = ""
    pending_audio_format: str = "wav"


class SessionAgent:
    def __init__(self, asr: ASRProvider, tts: TTSProvider, llm: LLMProvider) -> None:
        self.asr = asr
        self.tts = tts
        self.llm = llm
        self._sessions: dict[str, SessionState] = {}

    def _get_state(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    async def handle(self, event: EventEnvelope, emit: Emit) -> None:
        """Process one client event, sending each reply as soon as it's ready.

        Turns stream results out incrementally (asr.final as soon as ASR
        finishes, agent.text as soon as the LLM finishes, agent.audio only
        once TTS finishes) instead of buffering everything and sending it all
        at the end — the mobile client can then show the transcript/reply
        text noticeably before the audio arrives, instead of the whole turn
        appearing to hang until every stage (ASR + LLM + TTS) is done.
        """
        state = self._get_state(event.session_id)
        now = int(time.time() * 1000)

        if event.type == "session.start":
            state.mode = choose_mode(event.payload)
            await emit(
                OutboundEvent(
                    type="session.ack",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now,
                    payload={
                        "providerRoute": {
                            "asr": settings.asr_provider,
                            "tts": settings.tts_provider,
                            "llm": settings.llm_provider,
                        }
                    },
                )
            )
            return

        if event.type == "audio.chunk":
            audio_base64 = event.payload.get("audioBase64", "")
            audio_format = event.payload.get("format", "wav")
            # Buffer the audio for the upcoming audio.commit — for the current
            # one-shot recording flow the client sends the whole clip in a
            # single chunk, so we simply keep the latest value. `is_final`
            # False short-circuits every provider before any network call, so
            # this never actually costs a real ASR round trip.
            state.pending_audio_base64 = audio_base64
            state.pending_audio_format = audio_format
            transcript, confidence = await self.asr.transcribe_chunk(
                audio_base64,
                is_final=False,
                audio_format=audio_format,
            )
            state.last_partial_text = transcript
            await emit(
                OutboundEvent(
                    type="asr.partial",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now,
                    payload={"text": transcript, "confidence": confidence},
                )
            )
            return

        if event.type == "audio.commit":
            turn_started = time.perf_counter()

            asr_started = time.perf_counter()
            learner_text, confidence = await self.asr.transcribe_chunk(
                state.pending_audio_base64,
                is_final=True,
                audio_format=state.pending_audio_format,
            )
            asr_elapsed = time.perf_counter() - asr_started
            state.pending_audio_base64 = ""
            await emit(
                OutboundEvent(
                    type="asr.final",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now,
                    payload={"text": learner_text, "confidence": confidence},
                )
            )

            llm_started = time.perf_counter()
            agent_reply = await self.llm.reply(learner_text=learner_text, history=state.history, mode=state.mode)
            llm_elapsed = time.perf_counter() - llm_started
            state.history.append({"role": "learner", "text": learner_text})
            state.history.append({"role": "agent", "text": agent_reply})
            await emit(
                OutboundEvent(
                    type="agent.text",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now + 10,
                    payload={"text": agent_reply},
                )
            )

            tts_started = time.perf_counter()
            audio_bytes = await self.tts.synthesize(agent_reply)
            tts_elapsed = time.perf_counter() - tts_started
            await emit(
                OutboundEvent(
                    type="agent.audio",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now + 20,
                    payload={
                        "audioBase64": base64.b64encode(audio_bytes).decode("utf-8"),
                        "sampleRate": self.tts.sample_rate,
                        "format": self.tts.audio_format,
                    },
                )
            )
            await emit(
                OutboundEvent(
                    type="avatar.cue",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now + 25,
                    payload={"visemeTimeline": [], "emotion": "encouraging"},
                )
            )
            await emit(
                OutboundEvent(
                    type="eval.feedback",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now + 30,
                    payload=evaluate_pronunciation(learner_text),
                )
            )

            total_elapsed = time.perf_counter() - turn_started
            logger.info(
                "voice turn timing session=%s asr=%.2fs llm=%.2fs tts=%.2fs total=%.2fs",
                event.session_id,
                asr_elapsed,
                llm_elapsed,
                tts_elapsed,
                total_elapsed,
            )
            return

        if event.type == "session.input_text":
            learner_text = event.payload.get("text", "").strip()
            if not learner_text:
                return
            agent_reply = await self.llm.reply(learner_text=learner_text, history=state.history, mode=state.mode)
            await emit(
                OutboundEvent(
                    type="agent.text",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now,
                    payload={"text": agent_reply},
                )
            )
            return

        if event.type == "session.stop":
            await emit(
                OutboundEvent(
                    type="session.end",
                    sessionId=event.session_id,
                    traceId=event.trace_id,
                    timestampMs=now,
                    payload={"durationSec": 0, "turnCount": len(state.history) // 2},
                )
            )
            return

        await emit(
            OutboundEvent(
                type="error",
                sessionId=event.session_id,
                traceId=event.trace_id,
                timestampMs=now,
                payload={"code": "UNSUPPORTED_EVENT", "message": f"Unsupported event: {event.type}"},
            )
        )
