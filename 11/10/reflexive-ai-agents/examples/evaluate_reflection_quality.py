from src.agent_reflexive import ReflexiveAgent
from src.reflection_layer import ReflectionLayer
from src.memory_manager import MemoryManager

def demo():
    agent = ReflexiveAgent(ReflectionLayer(), MemoryManager())
    tasks = [
        "Explain what a skill market among AI agents is.",
        "Give 3 risks of reflexive agents and how to mitigate them.",
        "Provide a 5-step checklist for integrating a reflection layer."
    ]
    for t in tasks:
        out = agent.run_once(t)
        print(f"\nTASK: {t}\nSCORE: {out['score']:.2f}\nHINT: {out['hint']}")

if __name__ == "__main__":
    demo()
