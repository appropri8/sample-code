from __future__ import annotations
from typing import List
from .agent_base import AgentBase

class SkillRegistry:
    def __init__(self):
        self._agents: List[AgentBase] = []

    def register(self, agent: AgentBase):
        self._agents.append(agent)

    def list_agents(self) -> List[AgentBase]:
        return list(self._agents)
