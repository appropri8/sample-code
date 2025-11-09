from src.agents import Agent
from src.vsp import SimpleEncoder, VectorSpaceProtocol, cosine
import numpy as np

# Create two agents with different local transforms
enc = SimpleEncoder(dim=128)
agent_a = Agent(name="AgentA", vocab=["order pizza", "check status", "cancel item"], encoder=enc)
agent_b = Agent(name="AgentB", vocab=["place order", "track order", "abort request"], encoder=enc)

# Random local space transforms to simulate different embedding spaces
rng = np.random.default_rng(42)
Qa, _ = np.linalg.qr(rng.normal(size=(128, 128)))
Qb, _ = np.linalg.qr(rng.normal(size=(128, 128)))
agent_a.space_transform = Qa
agent_b.space_transform = Qb

# Encode shared calibration phrases
calib_a_texts = ["order pizza", "check status", "cancel item"]
calib_b_texts = ["place order", "track order", "abort request"]
calib_a = agent_a.encode(calib_a_texts)
calib_b = agent_b.encode(calib_b_texts)

# Perform VSP handshake
vsp = VectorSpaceProtocol(similarity_threshold=0.85)
hs = vsp.handshake(calib_a, calib_b)

print(f"Alignment score (mean cosine after align): {hs['alignment_score']:.3f}")
R_b_to_a = hs["R_b_to_a"]

# Transmit a new message from A to B via protocol layer
new_msg = "check status"
msg_vec_a = agent_a.encode([new_msg])[0]
msg_vec_in_b_space = vsp.transmit(msg_vec_a, R_src_to_dst=None)  # A -> Protocol (identity for A)
# For B to understand A, map A vector into B's space by inverting the learned mapping.
# Since we solved R for B->A, approximate A->B as R^T (orthogonal).
msg_vec_in_b_local = R_b_to_a.T @ msg_vec_in_b_space

result = agent_b.receive(msg_vec_in_b_local)
print("B's understanding (norm proxy):", result["understanding_score"])

# Show semantic similarity agreement for sanity
calib_a_aligned = calib_b @ R_b_to_a.T
sims = [cosine(calib_a[i], calib_a_aligned[i]) for i in range(len(calib_a_texts))]
print("Per-pair cosines after align:", [round(s, 3) for s in sims])
