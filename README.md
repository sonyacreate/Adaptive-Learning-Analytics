# Kvant — Product Analytics: Adaptive Learning

Product Analytics / EdTech case based on a real adaptive-learning platform originally built as a diploma project.

## Business problem
How can an EdTech product use learning behavior to personalize tasks, detect weak topics, and improve learning outcomes?

The analysis focuses on **engagement, learning performance, weak-topic detection, and signals for an adaptive recommender**.

## Key findings
- 160 task attempts across 7 active dates.
- Mathematics: 117 attempts, **59.0% accuracy**.
- History: 36 attempts, **25.0% accuracy**.
- English: 7 attempts, 57.1% accuracy — too little data for a strong conclusion.
- Ancient World: 23 attempts, **17.4% accuracy** — a meaningful candidate for review.
- Difficulty 1: 125 attempts, 50.4% accuracy.
- Difficulty 2: 29 attempts, 58.6% accuracy.
- Difficulty 3: only 6 attempts, so 33.3% accuracy is not reliable evidence.

## Product conclusions
1. Topic accuracy should be combined with observation volume.
2. Low-performing, sufficiently observed topics are candidates for additional practice.
3. Difficulty alone is not enough to personalize learning.
4. The current data has no control group, so it cannot prove that recommendations caused better outcomes.
5. The next step is a controlled experiment: **baseline recommendations vs adaptive recommendations**.

## SQL demonstrated
CTEs, CASE WHEN, GROUP BY, conditional aggregation, window functions, RANK(), topic/subject aggregation, and minimum-volume guardrails.

See [sql/analytics.sql](sql/analytics.sql).

## Stack
Python · pandas · SQL · DuckDB/SQLite · Jupyter · matplotlib

## Repository
```
README.md
requirements.txt
kvant_product_analytics.py
sql/analytics.sql
data/
  daily_activity.csv
  subject_performance.csv
  topic_performance.csv
  topic_catalog.csv
  task_attempts.csv
```

## Data limitations
The current analytical slice contains one active student, 160 attempts, 7 active dates, and no randomized control group. Response-time values are zero in the source data. Therefore this portfolio case intentionally avoids causal claims and treats recommender effectiveness as a hypothesis for future testing.

## Recommended experiment
**Control:** baseline recommendation  
**Treatment:** adaptive recommendation using recency + topic accuracy + progress

Primary metrics: task completion, learning accuracy, repeat practice of weak topics, D7 retention.