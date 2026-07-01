from __future__ import annotations


def choose_mode(payload: dict) -> str:
    mode = payload.get("mode", "free_talk")
    if mode not in {"free_talk", "scenario", "shadowing"}:
        return "free_talk"
    return mode

