# Context Budgets for Long-Context GenAI Apps

Complete executable code samples for the article [Context Budgets: How to Decide What Your GenAI App Should Send to the Model](https://appropri8.io/blog/2026/07/09/context-budgets-long-context-genai/).

A small, dependency-free Python reference for a context budget layer: rank retrieved chunks, trim low-value content, respect a token budget, and explain (in a debug report) what went into the prompt and what was cut.

## Structure

```
context-budgets-long-context-genai/
├── main.py             # Loads chunks, packs them, prints the debug report
├── scorer.py           # Weighted inclusion score per chunk
├── packer.py           # Token budget, packing, prompt builder, debug report
├── sample_chunks.json  # Example retrieved chunks with scores and token counts
└── README.md
```

## Run it

```bash
cd 2026/07/09/context-budgets-long-context-genai
python main.py
```

No third-party packages are required. It runs on Python 3.10+.

## What you get

A debug report that shows exactly why each chunk was kept or dropped:

```
Context budget: 740/2000 tokens used

Included:
- pricing_policy_2026.md, score 0.83, 430 tokens
- refund_rules.md, score 0.78, 310 tokens

Excluded:
- brand_voice.md, score 0.42, reason: low relevance
- pricing_policy_2023.md, score 0.39, reason: stale
```

Followed by the assembled prompt block that would actually be sent to the model.

## How the scoring works

Each chunk is scored with a fixed-weight formula:

```
final_score =
    relevance     * 0.40
  + trust         * 0.20
  + freshness     * 0.15
  + user_need     * 0.15
  - conflict_risk * 0.10
```

The packer drops stale or irrelevant chunks first (on their own merits), then fills the remaining budget by score. You can tune the weights in `scorer.py` and the budget in `packer.py` to match your own context model.
