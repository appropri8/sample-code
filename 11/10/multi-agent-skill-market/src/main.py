from __future__ import annotations
from .skill_registry import SkillRegistry
from .market_manager import MarketManager
from .agent_base import AgentBase

def make_default_market():
    reg = SkillRegistry()
    reg.register(AgentBase("SummarizerAgent", {"summarize", "bullet", "write"}))
    reg.register(AgentBase("CoderAgent", {"code", "python", "generate"}))
    reg.register(AgentBase("AnalystAgent", {"analyze", "risk", "metrics"}))
    market = MarketManager(reg.list_agents())
    return market

def run(task: str):
    market = make_default_market()
    bids = market.collect_bids(task)
    decision = market.select(bids)
    winner = next((a for a in market.agents if a.name == decision.winner), None)
    output = winner.act(task) if winner else "No output."
    return {"task": task, "decision": decision.reason, "output": output, "bids": [b.__dict__ for b in bids]}

if __name__ == "__main__":
    print(run("Generate a bullet-point summary of reflexive agents."))
