from __future__ import annotations
from dataclasses import dataclass

@dataclass
class MarketDecision:
    winner: str
    reason: str
