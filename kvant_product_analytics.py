"""Kvant Product Analytics — reproducible portfolio analysis."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load_data():
    topics = pd.read_csv(DATA / "topic_performance.csv")
    subjects = pd.read_csv(DATA / "subject_performance.csv")
    difficulty = pd.read_csv(DATA / "difficulty_performance.csv")
    activity = pd.read_csv(DATA / "daily_activity.csv", parse_dates=["date"])
    return topics, subjects, difficulty, activity


def add_product_priority(topics):
    """Translate observed performance into review candidates."""
    result = topics.copy()

    def classify(row):
        if row["attempts"] < 5:
            return "insufficient_data"
        if row["attempts"] >= 10 and row["accuracy_pct"] < 40:
            return "high_review_priority"
        if row["accuracy_pct"] < 60:
            return "review"
        return "do_not_prioritize"

    result["recommendation_bucket"] = result.apply(classify, axis=1)
    return result


def build_recommendation_candidates(topics):
    """Keep the decision layer separate from descriptive metrics."""
    return (
        topics[
            topics["recommendation_bucket"].isin(
                ["high_review_priority", "review"]
            )
        ]
        .sort_values(["recommendation_bucket", "accuracy_pct", "attempts"])
        .loc[
            :,
            [
                "subject",
                "topic",
                "attempts",
                "accuracy_pct",
                "recommendation_bucket",
            ],
        ]
    )


topics, subjects, difficulty, activity = load_data()
topics = add_product_priority(topics)
candidates = build_recommendation_candidates(topics)

subjects["attempt_share_pct"] = (
    100 * subjects["attempts"] / subjects["attempts"].sum()
)
subjects["accuracy_pct"] = 100 * subjects["correct"] / subjects["attempts"]

print("=== DATASET ===")
print(f"Attempts represented: {int(topics['attempts'].sum())}")
print(f"Active dates: {activity['date'].nunique()}")
print(f"Total XP: {int(activity['xp_earned'].sum())}")

print("\n=== SUBJECT PERFORMANCE ===")
print(
    subjects[
        ["subject", "attempts", "correct", "accuracy_pct", "attempt_share_pct"]
    ]
    .sort_values("attempts", ascending=False)
    .round(1)
    .to_string(index=False)
)

print("\n=== DECISION LAYER: NEXT-TOPIC CANDIDATES ===")
print(
    candidates.round(1).to_string(index=False)
    if not candidates.empty
    else "No topics meet the current review rules."
)

print("\n=== DIFFICULTY ===")
print(difficulty.round(1).to_string(index=False))

daily = activity.sort_values("date").copy()
daily["cumulative_xp"] = daily["xp_earned"].cumsum()
daily["tasks_change_vs_previous_day"] = daily["tasks_completed"].diff()

print("\n=== ACTIVITY ===")
print(daily.to_string(index=False))

weighted_accuracy = 100 * topics["correct"].sum() / topics["attempts"].sum()
print("\n=== PRODUCT INTERPRETATION ===")
print(f"Weighted accuracy across topic data: {weighted_accuracy:.1f}%")
print(
    "Recommendation is a hypothesis based on performance and observation volume; "
    "recency and progress require event-level data."
)
print(
    "The current slice has no control group, so recommender effectiveness "
    "cannot be treated as a causal result."
)

ax = (
    subjects.sort_values("accuracy_pct")
    .plot(
        x="subject",
        y="accuracy_pct",
        kind="barh",
        figsize=(8, 4),
        legend=False,
        title="Accuracy by subject",
    )
)
ax.set_xlabel("Accuracy, %")
plt.tight_layout()
plt.show()
