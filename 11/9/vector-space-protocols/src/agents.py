from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np

@dataclass
class Agent:
    name: str
    vocab: List[str]
    encoder: Any  # object with encode(List[str]) -> np.ndarray
    space_transform: np.ndarray = field(default_factory=lambda: np.eye(128))

    def encode(self, texts: List[str]) -> np.ndarray:
        vecs = self.encoder.encode(texts)
        # map into agent's local space
        return (self.space_transform @ vecs.T).T

    def receive(self, vector: np.ndarray) -> Dict[str, Any]:
        # For demo: store last received and return a basic "understanding score"
        score = float(np.linalg.norm(vector))
        return {"agent": self.name, "understanding_score": score}
