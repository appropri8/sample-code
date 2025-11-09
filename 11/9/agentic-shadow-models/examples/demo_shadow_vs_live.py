import json, pathlib
from src.shadow import ShadowModel
from src.agents import Planner, Executor

def main():
    data_path = pathlib.Path(__file__).resolve().parents[1] / "data" / "sample_executor_pairs.jsonl"
    pairs = [json.loads(l) for l in open(data_path, "r", encoding="utf-8")]

    X = [p["input"] for p in pairs]
    y = [p["output"] for p in pairs]

    shadow = ShadowModel().fit(X, y)
    planner = Planner(shadow=shadow, executor=Executor())

    queries = [
        "get order status #123",
        "ETA for #888",
        "cancel order #777",
        "please change address for #999",
        "refund order #321",
        "track status of #222"
    ]

    for q in queries:
        res = planner.ask(q, min_conf=0.68)
        print(f"Q: {q}\n -> ({res['source']}, conf={res['confidence']:.2f}) {res['answer']}\n")

if __name__ == "__main__":
    main()
