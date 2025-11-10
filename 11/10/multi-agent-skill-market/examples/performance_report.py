from src.main import make_default_market
import statistics as stats

def main():
    market = make_default_market()
    tasks = [
        "Generate a bullet-point summary of reflexive agents.",
        "Analyze top 3 risks in multi-agent markets.",
        "Write python code to generate a CSV file.",
        "Summarize research findings in 5 bullets.",
        "Provide risk metrics for a small project."
    ]
    scores = []
    for t in tasks:
        bids = market.collect_bids(t)
        decision = market.select(bids)
        print(f"TASK: {t}\nDECISION: {decision.reason}\n")
        # proxy score: number of bids as coverage metric
        scores.append(len(bids))
    print(f"Avg bid coverage: {stats.mean(scores):.2f} agents per task")

if __name__ == "__main__":
    main()
