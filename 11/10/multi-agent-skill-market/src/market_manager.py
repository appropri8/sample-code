from __future__ import annotations
import os
from typing import List, Tuple
from .agent_base import AgentBase, Bid
from .bidding_protocol import MarketDecision

class MarketManager:
    def __init__(self, agents: List[AgentBase]):
        self.agents = agents
        self.live = bool(os.getenv("OPENAI_API_KEY"))

    def collect_bids(self, task: str) -> List[Bid]:
        bids = []
        for a in self.agents:
            if a.can_handle(task):
                bids.append(a.bid(task))
        return bids

    def select(self, bids: List[Bid]) -> MarketDecision:
        if not bids:
            return MarketDecision("None", "No suitable agents bid.")

        # Score: utility * confidence - 0.2 * cost (transparent heuristic)
        scored = [(b.agent_name, b.utility * b.confidence - 0.2 * b.cost, b) for b in bids]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_name, best_score, best_bid = scored[0]
        reason = (f"Selected {best_name} with score {best_score:.2f}. "
                  f"Rationale: {best_bid.rationale} (u={best_bid.utility:.2f}, "
                  f"c={best_bid.confidence:.2f}, cost={best_bid.cost:.2f}).")
        return MarketDecision(best_name, reason)
