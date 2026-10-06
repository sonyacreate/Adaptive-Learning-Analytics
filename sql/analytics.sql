-- Kvant Product Analytics SQL layer
-- Source tables: topic_performance, subject_performance, daily_activity

-- 1. Subject performance + share of all attempts
WITH metrics AS (
    SELECT
        subject,
        attempts,
        correct,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct
    FROM subject_performance
)
SELECT
    subject,
    attempts,
    correct,
    accuracy_pct,
    ROUND(100.0 * attempts / SUM(attempts) OVER (), 1) AS attempt_share_pct
FROM metrics
ORDER BY attempts DESC;

-- 2. Weak topics with a minimum-volume guardrail
WITH topic_metrics AS (
    SELECT
        subject,
        topic_id,
        topic,
        attempts,
        correct,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct
    FROM topic_performance
)
SELECT
    subject,
    topic_id,
    topic,
    attempts,
    correct,
    accuracy_pct
FROM topic_metrics
WHERE attempts >= 10
  AND accuracy_pct < 60
ORDER BY accuracy_pct ASC, attempts DESC;

-- 3. Rank the weakest topics inside each subject
WITH topic_metrics AS (
    SELECT
        subject,
        topic,
        attempts,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct
    FROM topic_performance
    WHERE attempts >= 5
)
SELECT
    subject,
    topic,
    attempts,
    accuracy_pct,
    RANK() OVER (
        PARTITION BY subject
        ORDER BY accuracy_pct ASC, attempts DESC
    ) AS weakness_rank
FROM topic_metrics
ORDER BY subject, weakness_rank;

-- 4. Compare each topic with the average performance of its subject
WITH subject_metrics AS (
    SELECT
        subject,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS subject_accuracy_pct
    FROM subject_performance
),
topic_metrics AS (
    SELECT
        subject,
        topic,
        attempts,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS topic_accuracy_pct
    FROM topic_performance
)
SELECT
    t.subject,
    t.topic,
    t.attempts,
    t.topic_accuracy_pct,
    s.subject_accuracy_pct,
    ROUND(t.topic_accuracy_pct - s.subject_accuracy_pct, 1) AS gap_vs_subject_pp
FROM topic_metrics t
JOIN subject_metrics s
    ON t.subject = s.subject
WHERE t.attempts >= 5
ORDER BY gap_vs_subject_pp ASC;

-- 5. Turn the analytical rule into recommendation candidates
WITH topic_metrics AS (
    SELECT
        subject,
        topic,
        attempts,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct
    FROM topic_performance
)
SELECT
    subject,
    topic,
    attempts,
    accuracy_pct,
    CASE
        WHEN attempts < 5 THEN 'insufficient_data'
        WHEN attempts >= 10 AND accuracy_pct < 40 THEN 'high_review_priority'
        WHEN attempts >= 5 AND accuracy_pct < 60 THEN 'review'
        ELSE 'do_not_prioritize'
    END AS recommendation_bucket
FROM topic_metrics
ORDER BY
    CASE
        WHEN attempts >= 10 AND accuracy_pct < 40 THEN 1
        WHEN attempts >= 5 AND accuracy_pct < 60 THEN 2
        WHEN attempts < 5 THEN 3
        ELSE 4
    END,
    accuracy_pct ASC;

-- 6. Daily activity with cumulative XP and day-over-day task change
WITH activity AS (
    SELECT
        date,
        tasks_completed,
        xp_earned,
        LAG(tasks_completed) OVER (ORDER BY date) AS previous_day_tasks
    FROM daily_activity
)
SELECT
    date,
    tasks_completed,
    xp_earned,
    SUM(xp_earned) OVER (
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_xp,
    tasks_completed - previous_day_tasks AS tasks_change_vs_previous_day
FROM activity
ORDER BY date;

-- 7. Overall accuracy represented by the topic table
SELECT
    SUM(attempts) AS attempts,
    SUM(correct) AS correct_answers,
    ROUND(100.0 * SUM(correct) / NULLIF(SUM(attempts), 0), 1) AS accuracy_pct
FROM topic_performance;

-- 8. Decision layer: choose review candidates with explainable rules
-- This is a recommendation hypothesis, not a production ranking model.
WITH candidates AS (
    SELECT
        subject,
        topic_id,
        topic,
        attempts,
        ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct,
        CASE
            WHEN attempts < 5 THEN 'insufficient_data'
            WHEN attempts >= 10 AND 100.0 * correct / NULLIF(attempts, 0) < 40
                THEN 'high_review_priority'
            WHEN 100.0 * correct / NULLIF(attempts, 0) < 60
                THEN 'review'
            ELSE 'do_not_prioritize'
        END AS recommendation_bucket
    FROM topic_performance
)
SELECT
    subject,
    topic_id,
    topic,
    attempts,
    accuracy_pct,
    recommendation_bucket,
    CASE recommendation_bucket
        WHEN 'high_review_priority' THEN 'low_accuracy_with_enough_observations'
        WHEN 'review' THEN 'below_target_accuracy'
        WHEN 'insufficient_data' THEN 'collect_more_observations'
        ELSE 'no_review_signal'
    END AS recommendation_reason
FROM candidates
WHERE recommendation_bucket <> 'do_not_prioritize'
ORDER BY
    CASE recommendation_bucket
        WHEN 'high_review_priority' THEN 1
        WHEN 'review' THEN 2
        ELSE 3
    END,
    accuracy_pct ASC,
    attempts DESC;
