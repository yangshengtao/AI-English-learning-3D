from __future__ import annotations


def evaluate_pronunciation(learner_text: str) -> dict:
    # MVP heuristic scoring; replace with dedicated speech scoring model later.
    token_count = max(len(learner_text.split()), 1)
    long_sentence_penalty = 0.1 if token_count > 12 else 0.0
    score = max(0.55, 0.85 - long_sentence_penalty)
    return {
        "pronunciationScore": round(score, 2),
        "tips": ["Try clearer stress on content words.", "Pause briefly between clauses."],
    }

