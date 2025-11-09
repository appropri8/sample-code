import json, pathlib
from src.shadow import ShadowModel

def test_shadow_learns_templates():
    data_path = pathlib.Path(__file__).resolve().parents[1] / "data" / "sample_executor_pairs.jsonl"
    pairs = [json.loads(l) for l in open(data_path, "r", encoding="utf-8")]
    X = [p["input"] for p in pairs]
    y = [p["output"] for p in pairs]

    model = ShadowModel().fit(X, y)
    pred, conf = model.predict("get order status #555")
    assert "in transit" in pred.lower()
    assert 0.0 <= conf <= 1.0
