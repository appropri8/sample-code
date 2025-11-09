from typing import List, Tuple, Dict, Any
import numpy as np

class SimpleEncoder:
    """Offline-friendly encoder that creates deterministic pseudo-embeddings.
    This avoids external models while preserving vector-space behavior.
    """
    def __init__(self, dim: int = 128, seed: int = 13):
        self.dim = dim
        rng = np.random.default_rng(seed)
        # build hash vectors for lowercase ascii chars for reproducibility
        self.char_map = {c: rng.normal(0, 1, size=dim) for c in "abcdefghijklmnopqrstuvwxyz "}

    def encode(self, texts: List[str]) -> np.ndarray:
        vecs = []
        for t in texts:
            v = np.zeros(self.dim)
            for ch in t.lower():
                v += self.char_map.get(ch, 0)
            # normalize
            n = np.linalg.norm(v) + 1e-9
            vecs.append(v / n)
        return np.vstack(vecs)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

class VectorSpaceProtocol:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def handshake(self, a_vecs: np.ndarray, b_vecs: np.ndarray) -> Dict[str, Any]:
        """Compute alignment transform for B to understand A (and vice versa) via Procrustes.
        Returns alignment quality and transforms.
        """
        # Solve for orthogonal matrix R minimizing ||A - B R||
        # Using SVD: R = U V^T where A^T B = U S V^T
        M = a_vecs.T @ b_vecs
        U, _, Vt = np.linalg.svd(M, full_matrices=False)
        R = U @ Vt
        aligned = b_vecs @ R.T
        mean_cos = float(np.mean([cosine(a_vecs[i], aligned[i]) for i in range(a_vecs.shape[0])]))
        return {"R_b_to_a": R, "alignment_score": mean_cos}

    def transmit(self, vec: np.ndarray, R_src_to_dst=None) -> np.ndarray:
        if R_src_to_dst is None:
            return vec
        return (R_src_to_dst @ vec.T).T
