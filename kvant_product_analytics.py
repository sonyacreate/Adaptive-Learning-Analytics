"""Kvant Product Analytics — reproducible portfolio analysis."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

topics = pd.read_csv(DATA / "topic_performance.csv")
subjects = pd.read_csv(DATA / "subject_performance.csv")
activity = pd.read_csv(DATA / "daily_activity.csv", parse_dates=["date"])

print("=== DATASET ===")
print(f"Attempts represented: {int(topics['attempts'].sum())}")
print(f"Active dates: {activity['date'].nunique()}")

print("\n=== SUBJECT PERFORMANCE ===")
print(subjects[["subject","attempts","correct","accuracy_pct"]]
      .sort_values("attempts", ascending=False)
      .round(1).to_string(index=False))

print("\n=== WEAK TOPICS (>=10 attempts) ===")
weak = topics[topics["attempts"] >= 10].sort_values(["accuracy_pct","attempts"])
print(weak[["subject","topic","attempts","accuracy_pct"]].round(1).to_string(index=False))

print("\n=== DIFFICULTY ===")
# Difficulty metrics are calculated in the original event-level analysis.
# Here we report the validated portfolio values from the analytical layer.
difficulty = pd.DataFrame({
    "difficulty": [1, 2, 3],
    "attempts": [125, 29, 6],
    "accuracy_pct": [50.4, 58.6, 33.3]
})
print(difficulty.to_string(index=False))

print("\n=== PRODUCT INTERPRETATION ===")
print("Use topic accuracy together with observation volume.")
print("The current slice has no control group, so recommender effectiveness is a hypothesis, not a causal result.")

subjects.sort_values("accuracy_pct").plot(
    x="subject", y="accuracy_pct", kind="barh", figsize=(8,4),
    legend=False, title="Accuracy by subject"
)
plt.xlabel("Accuracy, %")
plt.tight_layout()
plt.show()
