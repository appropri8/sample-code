from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MemoryEntry:
    task: str
    answer: str
    critique: str
    score: float
    hint: str

class MemoryManager:
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self._entries: List[MemoryEntry] = []

    def add_reflection(self, entry: MemoryEntry):
        self._entries.append(entry)
        if len(self._entries) > self.capacity:
            self._entries.pop(0)

    def latest_policy_hint(self) -> Optional[str]:
        # Return the best recent hint (naive: highest score among last 5)
        recent = self._entries[-5:]
        if not recent:
            return None
        best = max(recent, key=lambda e: e.score)
        return best.hint
