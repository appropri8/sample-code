"""Pack scored chunks into a token budget and build the final prompt block.

The packer answers one question: given a token budget for retrieved evidence,
which chunks get in, which get cut, and why?
"""

from scorer import score_chunk

# Token budget for the retrieved-evidence slice of the prompt.
# This is the "Retrieved evidence: 50%" slice of a 4096-token context budget.
EVIDENCE_BUDGET = 2000

# Hard floors. A chunk below these is excluded on its own merits, not because
# of budget pressure. Stale evidence and irrelevant evidence are noise.
FRESHNESS_FLOOR = 0.5  # below this => "stale"
RELEVANCE_FLOOR = 0.4  # below this => "low relevance"


def _exclude_reason(chunk: dict) -> str:
    if chunk["freshness"] < FRESHNESS_FLOOR:
        return "stale"
    if chunk["relevance"] < RELEVANCE_FLOOR:
        return "low relevance"
    return "over budget"


def pack(chunks: list[dict], budget: int = EVIDENCE_BUDGET):
    """Return (included, excluded, tokens_used).

    Tier 0 (system rules) and Tier 1 (user request) are mandatory and live
    outside the retrieved-evidence pool, so we only pack chunks at tier >= 2.
    Hard-fail chunks (stale / low relevance) are dropped first, then the rest
    are filled in by score until the budget runs out.
    """
    scored = [{**c, "score": score_chunk(c)} for c in chunks]
    evidence = [c for c in scored if c.get("tier", 2) >= 2]

    included, excluded = [], []
    used = 0
    for c in sorted(evidence, key=lambda x: x["score"], reverse=True):
        if c["freshness"] < FRESHNESS_FLOOR or c["relevance"] < RELEVANCE_FLOOR:
            c["reason"] = _exclude_reason(c)
            excluded.append(c)
        elif used + c["tokens"] <= budget:
            included.append(c)
            used += c["tokens"]
        else:
            c["reason"] = "over budget"
            excluded.append(c)
    return included, excluded, used


def build_prompt(included: list[dict], system: str, user_request: str) -> str:
    """Assemble the final prompt from the kept chunks plus fixed blocks."""
    lines = [
        system,
        "",
        "User request:",
        user_request,
        "",
        "Retrieved evidence:",
    ]
    for c in included:
        lines.append(f"- [{c['id']}] {c['text']}")
    return "\n".join(lines)


def debug_report(included, excluded, used, budget: int = EVIDENCE_BUDGET) -> str:
    """Plain-text report of what went in, what was cut, and why."""
    out = [f"Context budget: {used}/{budget} tokens used", "", "Included:"]
    for c in included:
        out.append(f"- {c['id']}, score {c['score']}, {c['tokens']} tokens")
    out.append("")
    out.append("Excluded:")
    for c in excluded:
        out.append(f"- {c['id']}, score {c['score']}, reason: {c['reason']}")
    return "\n".join(out)
