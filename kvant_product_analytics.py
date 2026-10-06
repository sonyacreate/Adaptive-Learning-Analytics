"""Kvant Product Analytics — reproducible portfolio analysis.

The script keeps three layers separate:
1. data validation,
2. descriptive metrics,
3. an explainable recommendation rule.

The recommendation rule is a product hypothesis, not a production model.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


REQUIRED_TOPIC_COLUMNS = {"subject", "topic", "attempts", "correct", "accuracy_pct"}
REQUIRED_SUBJECT_COLUMNS = {"subject", "attempts", "correct"}
REQUIRED_DIFFICULTY_COLUMNS = {"difficulty", "attempts", "correct"}
REQUIRED_ACTIVITY_COLUMNS = {"date", "tasks_completed", "xp_earned"}


def load_data():
    """Load prepared analytical tables from the repository."""
    topics = pd.read_csv(DATA / "topic_performance.csv")
    subjects = pd.read_csv(DATA / "subject_performance.csv")
    difficulty = pd.read_csv(DATA / "difficulty_performance.csv")
    activity = pd.read_csv(
        DATA / "daily_activity.csv",
        parse_dates=["date"],
    )
    return topics, subjects, difficulty, activity


def validate_columns(df, required, table_name):
    """Fail early when the analytical input schema changes."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{table_name}: missing required columns: {sorted(missing)}"
        )


def validate_metrics(topics, subjects, difficulty, activity):
    """Check basic analytical invariants before calculating metrics."""
    validate_columns(topics, REQUIRED_TOPIC_COLUMNS, "topic_performance")
    validate_columns(subjects, REQUIRED_SUBJECT_COLUMNS, "subject_performance")
    validate_columns(difficulty, REQUIRED_DIFFICULTY_COLUMNS, "difficulty_performance")
    validate_columns(activity, REQUIRED_ACTIVITY_COLUMNS, "daily_activity")

    for name, df in {
        "topic_performance": topics,
        "subject_performance": subjects,
        "difficulty_performance": difficulty,
    }.items():
        if (df["attempts"] <= 0).any():
            raise ValueError(f"{name}: attempts must be positive.")
        if (df["correct"] < 0).any() or (df["correct"] > df["attempts"]).any():
            raise ValueError(f"{name}: correct must be between 0 and attempts.")

    if (activity["tasks_completed"] < 0).any() or (activity["xp_earned"] < 0).any():
        raise ValueError("daily_activity: tasks_completed and xp_earned must be non-negative.")

    calculated_topic_accuracy = 100 * topics["correct"] / topics["attempts"]
    if not calculated_topic_accuracy.round(10).eq(
        topics["accuracy_pct"].round(10)
    ).all():
        raise ValueError(
            "topic_performance: accuracy_pct is inconsistent with correct / attempts."
        )

    if activity["date"].duplicated().any():
        raise ValueError("daily_activity: date must be unique.")


def add_product_priority(topics):
    """Translate performance and observation volume into an explainable rule."""
    result = topics.copy()

    result["recommendation_bucket"] = "do_not_prioritize"
    result.loc[result["attempts"] < 5, "recommendation_bucket"] = "insufficient_data"
    result.loc[
        (result["attempts"] >= 5) & (result["accuracy_pct"] < 60),
        "recommendation_bucket",
    ] = "review"
    result.loc[
        (result["attempts"] >= 10) & (result["accuracy_pct"] < 40),
        "recommendation_bucket",
    ] = "high_review_priority"

    result["recommendation_reason"] = result["recommendation_bucket"].map(
        {
            "high_review_priority": "low_accuracy_with_enough_observations",
            "review": "below_target_accuracy",
            "insufficient_data": "collect_more_observations",
            "do_not_prioritize": "no_review_signal",
        }
    )
    return result


def build_recommendation_candidates(topics):
    """Return only actionable review candidates."""
    return (
        topics[
            topics["recommendation_bucket"].isin(
                ["high_review_priority", "review"]
            )
        ]
        .sort_values(
            ["recommendation_bucket", "accuracy_pct", "attempts"],
            ascending=[True, True, False],
        )
        [
            [
                "subject",
                "topic",
                "attempts",
                "accuracy_pct",
                "recommendation_bucket",
                "recommendation_reason",
            ]
        ]
    )


def prepare_subject_metrics(subjects):
    """Calculate subject-level accuracy and share without relying on precomputed values."""
    result = subjects.copy()
    total_attempts = result["attempts"].sum()
    result["accuracy_pct"] = 100 * result["correct"] / result["attempts"]
    result["attempt_share_pct"] = 100 * result["attempts"] / total_attempts
    return result


def prepare_daily_activity(activity):
    """Add trend-oriented metrics while preserving the source data."""
    result = activity.sort_values("date").copy()
    result["cumulative_xp"] = result["xp_earned"].cumsum()
    result["tasks_change_vs_previous_day"] = result["tasks_completed"].diff()
    return result


def print_report(topics, subjects, difficulty, activity):
    """Print the analytical output used for a portfolio run."""
    subjects = prepare_subject_metrics(subjects)
    topics = add_product_priority(topics)
    candidates = build_recommendation_candidates(topics)
    daily = prepare_daily_activity(activity)

    print("=== DATASET ===")
    print(f"Attempts represented: {int(topics['attempts'].sum())}")
    print(f"Topics represented: {topics['topic'].nunique()}")
    print(f"Subjects represented: {subjects['subject'].nunique()}")
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
    if candidates.empty:
        print("No topics meet the current review rules.")
    else:
        print(candidates.round(1).to_string(index=False))

    print("\n=== DIFFICULTY ===")
    print(difficulty.round(1).to_string(index=False))

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
        "The current slice has no control group, so recommendation effectiveness "
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


def main():
    topics, subjects, difficulty, activity = load_data()
    validate_metrics(topics, subjects, difficulty, activity)
    print_report(topics, subjects, difficulty, activity)


if __name__ == "__main__":
    main()
