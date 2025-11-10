from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
from .memory_manager import MemoryManager, MemoryEntry
from .reflection_layer import ReflectionLayer

class ReflexiveAgent:
    """A simple reflexive agent that performs a task, observes results,
    reflects on its own reasoning, then updates its memory/policy hints."""

    def __init__(self, reflection: ReflectionLayer, memory: Optional[MemoryManager] = None):
        self.reflection = reflection
        self.memory = memory or MemoryManager()

    # --- mock "LLM" ---
    def _call_llm(self, prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Mock response for offline use
            return ("[MOCK-LLM]
"
                    "Thoughts: I'll provide a clear, structured answer.
"
                    "Answer: Reflexive agents improve reliability by critiquing their own steps and adapting policies.
")
        # Live call (optional)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[LLM-ERROR] {e}"

    def perceive_and_act(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Perceive environment + memory, produce an action (answer)."""
        policy_hints = self.memory.latest_policy_hint()
        prompt = f"""Task: {task}
Context: {context or "N/A"}
Policy hints: {policy_hints or "None"}
Please produce a helpful, concise answer with bullet points if appropriate.
"""
        answer = self._call_llm(prompt)
        observation = f"User received answer of length {len(answer)}."
        return {
            "task": task,
            "answer": answer,
            "observation": observation,
            "policy_hints": policy_hints,
        }

    def reflect_and_update(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Run reflection, score, and update memory/policy."""
        critique, score, hint = self.reflection.critique(
            task=step["task"],
            answer=step["answer"],
            observation=step["observation"]
        )
        self.memory.add_reflection(MemoryEntry(
            task=step["task"],
            answer=step["answer"],
            critique=critique,
            score=score,
            hint=hint,
        ))
        return {"critique": critique, "score": score, "hint": hint}

    def run_once(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        step = self.perceive_and_act(task, context)
        refl = self.reflect_and_update(step)
        return {**step, **refl}
