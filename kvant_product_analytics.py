"""Kvant Product Analytics — reproducible portfolio analysis."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

attempts = pd.read_csv(DATA / "task_attempts.csv", parse_dates=["created_at"])

subject_metrics = (
    attempts.groupby("subject")
    .agg(attempts=("attempt_id","count"),
         correct=("is_correct","sum"),
         accuracy=("is_correct","mean"))
    .sort_values("attempts", ascending=False)
)
subject_metrics["accuracy_pct"] = subject_metrics["accuracy"] * 100

topic_metrics = (
    attempts.groupby(["subject","topic_id","topic"])
    .agg(attempts=("attempt_id","count"),
         correct=("is_correct","sum"),
         accuracy=("is_correct","mean"),
         last_attempt=("created_at","max"))
    .reset_index()
)
topic_metrics["accuracy_pct"] = topic_metrics["accuracy"] * 100

difficulty_metrics = (
    attempts.groupby("difficulty")
    .agg(attempts=("attempt_id","count"),
         accuracy=("is_correct","mean"))
    .reset_index()
)
difficulty_metrics["accuracy_pct"] = difficulty_metrics["accuracy"] * 100

daily = (
    attempts.assign(activity_date=attempts["created_at"].dt.date)
    .groupby("activity_date")
    .agg(attempts=("attempt_id","count"),
         accuracy=("is_correct","mean"))
    .reset_index()
)
daily["accuracy_pct"] = daily["accuracy"] * 100

print("=== DATASET ===")
print(f"Attempts: {len(attempts)}")
print(f"Active dates: {attempts['created_at'].dt.date.nunique()}")

print("\n=== SUBJECT PERFORMANCE ===")
print(subject_metrics[["attempts","correct","accuracy_pct"]].round(1))

print("\n=== WEAK TOPICS (>=10 attempts) ===")
weak = topic_metrics[topic_metrics["attempts"] >= 10].sort_values("accuracy")
print(weak[["subject","topic","attempts","accuracy_pct"]].round(1).to_string(index=False))

print("\n=== DIFFICULTY ===")
print(difficulty_metrics.round(1).to_string(index=False))

# Recruiter-friendly visualization
subject_metrics["accuracy_pct"].sort_values().plot(
    kind="barh", figsize=(8,4), title="Accuracy by subject"
)
plt.xlabel("Accuracy, %")
plt.tight_layout()
plt.show()
