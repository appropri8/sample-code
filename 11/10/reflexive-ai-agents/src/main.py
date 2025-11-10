from __future__ import annotations
from .agent_reflexive import ReflexiveAgent
from .reflection_layer import ReflectionLayer
from .memory_manager import MemoryManager

def run(task: str, context: str | None = None):
    agent = ReflexiveAgent(reflection=ReflectionLayer(), memory=MemoryManager())
    result = agent.run_once(task, context)
    return result

if __name__ == "__main__":
    print(run("Explain reflexive AI agents in 5 bullet points."))
