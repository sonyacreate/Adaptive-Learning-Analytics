-- Kvant Product Analytics SQL layer
-- Source tables:
--   topic_performance, subject_performance, daily_activity
--
-- The SQL is intentionally written as an analytical layer:
-- raw counts -> derived metrics -> guarded decision rules.
-- Important: threshold filters use the raw ratio, not rounded accuracy.

-- 0. Data quality / metric consistency checks
SELECT
    COUNT(*) AS topic_rows,
    SUM(CASE WHEN attempts <= 0 THEN 1 ELSE 0 END) AS invalid_attempt_rows,
    SUM(CASE WHEN correct < 0 OR correct > attempts THEN 1 ELSE 0 END) AS invalid_correct_rows,
    SUM(
        CASE
            WHEN ABS(accuracy_pct - 100.0 * correct / NULLIF(attempts, 0)) > 0.01
            THEN 1 ELSE 0
        END
    ) AS inconsistent_accuracy_rows
FROM topic_performance;

-- 1. Subject performance + share of all attempts
WITH metrics AS (
    SELECT
        subject,
        attempts,
        correct,
        100.0 * correct / NULLIF(attempts, 0) AS accuracy_pct
    FROM subject_performance
)
SELECT
    subject,
    attempts,
    correct,
    ROUND(accuracy_pct, 1) AS accuracy_pct,
    ROUND(100.0 * attempts / SUM(attempts) OVER (), 1) AS attempt_share_pct
FROM metrics
ORDER BY attempts DESC;

-- 2. Weak topics with a minimum-volume guardrail
-- Do not filter on rounded accuracy: 39.96% must remain below a 40% threshold.
SELECT
    subject,
    topic_id,
    topic,
    attempts,
    correct,
    ROUND(100.0 * correct / NULLIF(attempts, 0), 1) AS accuracy_pct
FROM topic_performance
WHERE attempts >= 10
  AND 100.0 * correct / NULLIF(attempts, 0) < 60
ORDER BY accuracy_pct ASC, attempts DESC;

-- 3. Rank the weakest topics inside each subject
WITH topic_metrics AS (
    SELECT
        subject,
        topic,
        attempts,
        100.0 * correct / NULLIF(attempts, 0) AS accuracy_pct
    FROM topic_performance
    WHERE attempts >= 5
)
SELECT
    subject,
    topic,
    attempts,
    ROUND(accuracy_pct, 1) AS accuracy_pct,
    RANK() OVER (
        PARTITION BY subject
        ORDER BY accuracy_pct ASC, attempts DESC
    ) AS weakness_rank
FROM topic_metrics
ORDER BY subject, weakness_rank;

-- 4. Compare each topic with subject-level performance
WITH subject_metrics AS (
    SELECT
        subject,
        100.0 * correct / NULLIF(attempts, 0) AS subject_accuracy_pct
    FROM subject_performance
),
topic_metrics AS (
    SELECT
        subject,
        topic,
        attempts,
        100.0 * correct / NULLIF(attempts, 0) AS topic_accuracy_pct
    FROM topic_performance
)
SELECT
    t.subject,
    t.topic,
    t.attempts,
    ROUND(t.topic_accuracy_pct, 1) AS topic_accuracy_pct,
    ROUND(s.subject_accuracy_pct, 1) AS subject_accuracy_pct,
    ROUND(t.topic_accuracy_pct - s.subject_accuracy_pct, 1) AS gap_vs_subject_pp
FROM topic_metrics t
JOIN subject_metrics s
    ON t.subject = s.subject
WHERE t.attempts >= 5
ORDER BY gap_vs_subject_pp ASC;

-- 5. Decision layer: one source of truth for recommendation buckets
WITH scored_topics AS (
    SELECT
        subject,
        topic_id,
        topic,
        attempts,
        100.0 * correct / NULLIF(attempts, 0) AS accuracy_pct
    FROM topic_performance
),
classified AS (
    SELECT
        subject,
        topic_id,
        topic,
        attempts,
        accuracy_pct,
        CASE
            WHEN attempts < 5 THEN 'insufficient_data'
            WHEN attempts >= 10 AND accuracy_pct < 40 THEN 'high_review_priority'
            WHEN accuracy_pct < 60 THEN 'review'
            ELSE 'do_not_prioritize'
        END AS recommendation_bucket
    FROM scored_topics
)
SELECT
    subject,
    topic_id,
    topic,
    attempts,
    ROUND(accuracy_pct, 1) AS accuracy_pct,
    recommendation_bucket,
    CASE recommendation_bucket
        WHEN 'high_review_priority' THEN 'low_accuracy_with_enough_observations'
        WHEN 'review' THEN 'below_target_accuracy'
        WHEN 'insufficient_data' THEN 'collect_more_observations'
        ELSE 'no_review_signal'
    END AS recommendation_reason
FROM classified
ORDER BY
    CASE recommendation_bucket
        WHEN 'high_review_priority' THEN 1
        WHEN 'review' THEN 2
        WHEN 'insufficient_data' THEN 3
        ELSE 4
    END,
    accuracy_pct ASC,
    attempts DESC;

-- 6. Daily activity: trend + cumulative XP
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
    ROUND(
        100.0 * SUM(correct) / NULLIF(SUM(attempts), 0),
        1
    ) AS accuracy_pct
FROM topic_performance;
