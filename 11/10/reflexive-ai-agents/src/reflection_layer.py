from __future__ import annotations
import os
import re
from typing import Tuple

class ReflectionLayer:
    """Naive reflection layer that can optionally call an LLM for critique.
    Returns (critique, score, hint)."""
    def __init__(self):
        self.live = bool(os.getenv("OPENAI_API_KEY"))

    def _mock_critique(self, task: str, answer: str, observation: str) -> Tuple[str, float, str]:
        # Simple heuristics: longer answers and bullet points score better
        score = 0.0
        if len(answer) > 120: score += 0.4
        if re.search(r"\n-\s", answer): score += 0.3
        if "clear" in answer.lower() or "structured" in answer.lower(): score += 0.2
        if "error" in answer.lower(): score -= 0.3
        score = max(0.0, min(1.0, score))

        critique = (
            "Clarity is decent. Consider adding a short list of key takeaways and an example. "
            "Avoid generic phrasing; tailor the answer to the task explicitly."
        )
        hint = "Prefer bullet points + example; keep to 5–7 lines; bold key terms."
        return critique, score, hint

    def _llm_critique(self, task: str, answer: str, observation: str) -> Tuple[str, float, str]:
        try:
            from openai import OpenAI
            client = OpenAI()
            prompt = f"""You are a critical writing coach for AI agent outputs.
Task: {task}
Answer:
{answer}

Observation: {observation}

1) Provide a brief critique (<=80 words).
2) Give a score 0..1 for usefulness and clarity.
3) Provide one sentence of policy hint to improve the next answer."""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            ).choices[0].message.content
            # Extremely simple parse
            lines = [l.strip() for l in resp.splitlines() if l.strip()]
            critique = lines[0]
            score = 0.7
            hint = lines[-1]
            return critique, float(score), hint
        except Exception as e:
            return f"LLM critique failed: {e}", 0.5, "Fallback: emphasize brevity and bullets."

    def critique(self, task: str, answer: str, observation: str):
        if not self.live:
            return self._mock_critique(task, answer, observation)
        return self._llm_critique(task, answer, observation)
