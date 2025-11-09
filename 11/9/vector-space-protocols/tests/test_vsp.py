from src.vsp import SimpleEncoder, VectorSpaceProtocol, cosine
from src.agents import Agent
import numpy as np

def test_handshake_alignment_improves_similarity():
    enc = SimpleEncoder(dim=64)
    a = Agent("A", [], enc)
    b = Agent("B", [], enc)

    # Different local spaces
    rng = np.random.default_rng(0)
    Qa, _ = np.linalg.qr(rng.normal(size=(64,64)))
    Qb, _ = np.linalg.qr(rng.normal(size=(64,64)))
    a.space_transform = Qa
    b.space_transform = Qb

    texts = ["alpha", "beta", "gamma", "delta"]
    va = a.encode(texts)
    vb = b.encode(texts)

    # Before alignment
    pre = np.mean([cosine(va[i], vb[i]) for i in range(len(texts))])

    vsp = VectorSpaceProtocol()
    hs = vsp.handshake(va, vb)
    R = hs["R_b_to_a"]
    vb_aligned = vb @ R.T
    post = np.mean([cosine(va[i], vb_aligned[i]) for i in range(len(texts))])

    assert post > pre
