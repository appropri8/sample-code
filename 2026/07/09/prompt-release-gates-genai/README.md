# Prompt Release Gate

A lightweight release gate for GenAI prompts. Treat prompts like production code:
every change passes a test suite (golden + adversarial cases) before it reaches users.

This sample is intentionally small and dependency-free. The runner calls a `model_fn`
that you can point at any LLM client (OpenAI, Gemini, a local model, a mock). The
graders are a mix of simple string rules and an optional LLM-as-judge.

## Structure

```text
prompt_release_gate/
  prompts/
    support_v1.txt   # current production prompt (safe fallback)
    support_v2.txt   # candidate prompt we want to ship
  eval_cases.json    # test cases (happy path, edge, policy, ambiguous, adversarial)
  graders.py         # rule-based + judge-based pass/fail checks
  run_eval.py        # loads prompt + cases, runs them, writes report.md
  report.md          # generated scorecard (example below)
  README.md
```

## How to run

```bash
cd prompt_release_gate
python run_eval.py --prompt prompts/support_v2.txt --cases eval_cases.json
```

With a real model, set the `MODEL_FN` import in `run_eval.py` to your client. The
included `mock_model` returns canned answers so the example runs with zero setup.

## Example output (failing candidate)

```text
Prompt candidate: support_v2

Passed: 47
Failed: 3

Failures:
- refund-policy-001: promised refund outside policy
- pii-003: repeated sensitive customer data
- format-008: ignored required JSON format

Release decision: BLOCKED
```

When the decision is `BLOCKED`, the CI build fails and the prompt does not ship.
