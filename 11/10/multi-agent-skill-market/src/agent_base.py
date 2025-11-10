from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Bid:
    agent_name: str
    utility: float      # 0..1 estimate of usefulness
    confidence: float   # 0..1 confidence in the estimate
    cost: float         # abstract cost; lower is better
    rationale: str

class AgentBase:
    name: str
    skills: set[str]

    def __init__(self, name: str, skills: set[str]):
        self.name = name
        self.skills = skills

    def can_handle(self, task: str) -> bool:
        task_l = task.lower()
        return any(s in task_l for s in self.skills)

    def bid(self, task: str) -> Bid:
        # naive bid based on keyword matches
        matches = sum(1 for s in self.skills if s in task.lower())
        utility = min(1.0, 0.3 + 0.2 * matches)
        confidence = min(1.0, 0.5 + 0.1 * matches)
        cost = max(0.1, 1.0 - 0.2 * matches)
        rationale = f"Matches {matches} skill keyword(s): {', '.join(self.skills)}."
        return Bid(self.name, utility, confidence, cost, rationale)

    def act(self, task: str) -> str:
        return f"{self.name} handled task with skills {', '.join(sorted(self.skills))}. Output: [mock]"
