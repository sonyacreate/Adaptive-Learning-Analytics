-- Kvant Product Analytics SQL layer
-- Analytical source: topic_performance.csv / subject_performance.csv

-- Subject performance
SELECT subject, attempts, correct,
       ROUND(accuracy_pct, 1) AS accuracy_pct
FROM subject_performance
ORDER BY attempts DESC;

-- Weak topics with a minimum-volume guardrail
SELECT subject, topic_id, topic, attempts, correct,
       ROUND(accuracy_pct, 1) AS accuracy_pct
FROM topic_performance
WHERE attempts >= 10
ORDER BY accuracy_pct ASC, attempts DESC;

-- Aggregate accuracy represented by the topic table
SELECT
    SUM(attempts) AS attempts,
    SUM(correct) AS correct_answers,
    ROUND(100.0 * SUM(correct) / SUM(attempts), 1) AS accuracy_pct
FROM topic_performance;

-- Rank weak topics within each subject
SELECT subject, topic, attempts,
       ROUND(accuracy_pct, 1) AS accuracy_pct,
       RANK() OVER (
           PARTITION BY subject
           ORDER BY accuracy_pct ASC
       ) AS weakness_rank
FROM topic_performance
WHERE attempts >= 5
ORDER BY subject, weakness_rank;

-- Daily engagement
SELECT date, tasks_completed, xp_earned
FROM daily_activity
ORDER BY date;