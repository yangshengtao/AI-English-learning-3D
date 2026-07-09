from __future__ import annotations

from app.services.evaluation import evaluate_pronunciation
from app.services.lesson_planner import choose_mode


def test_choose_mode_defaults_to_free_talk_when_missing() -> None:
    assert choose_mode({}) == "free_talk"


def test_choose_mode_accepts_known_modes() -> None:
    assert choose_mode({"mode": "scenario"}) == "scenario"
    assert choose_mode({"mode": "shadowing"}) == "shadowing"


def test_choose_mode_rejects_unknown_mode() -> None:
    assert choose_mode({"mode": "not-a-real-mode"}) == "free_talk"


def test_evaluate_pronunciation_short_sentence_score() -> None:
    result = evaluate_pronunciation("Hello there")

    assert result["pronunciationScore"] == 0.85
    assert len(result["tips"]) == 2


def test_evaluate_pronunciation_long_sentence_penalty() -> None:
    long_sentence = " ".join(["word"] * 13)
    result = evaluate_pronunciation(long_sentence)

    assert result["pronunciationScore"] == 0.75
