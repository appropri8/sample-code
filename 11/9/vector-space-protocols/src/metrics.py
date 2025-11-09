import numpy as np

def vector_drift(history_a, history_b) -> float:
    """Mean cosine distance between corresponding messages over time."""
    if len(history_a) == 0: return 0.0
    sims = []
    for va, vb in zip(history_a, history_b):
        sims.append(cosine(va, vb))
    return float(np.mean([1 - s for s in sims]))

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def semantic_agreement_ratio(sims, threshold=0.85):
    """Fraction of pairs whose cosine >= threshold."""
    sims = np.asarray(sims)
    return float(np.mean(sims >= threshold))
