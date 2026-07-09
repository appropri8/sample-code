"""Score retrieved context chunks for inclusion in a prompt.

The score is a weighted mix of signals that matter in a long-context app:
relevance to the current request, source trust, evidence freshness,
user-specific need, and conflict risk.

This mirrors the formula from the article:

    final_score =
        relevance * 0.40 +
        trust     * 0.20 +
        freshness * 0.15 +
        user_need * 0.15 -
        conflict_risk * 0.10
"""

WEIGHTS = {
    "relevance": 0.40,
    "trust": 0.20,
    "freshness": 0.15,
    "user_need": 0.15,
    "conflict_risk": 0.10,  # applied as a penalty
}


def score_chunk(chunk: dict) -> float:
    """Return the inclusion score for a single chunk, rounded to 2 places."""
    score = (
        chunk["relevance"] * WEIGHTS["relevance"]
        + chunk["trust"] * WEIGHTS["trust"]
        + chunk["freshness"] * WEIGHTS["freshness"]
        + chunk["user_need"] * WEIGHTS["user_need"]
        - chunk["conflict_risk"] * WEIGHTS["conflict_risk"]
    )
    return round(score, 2)
