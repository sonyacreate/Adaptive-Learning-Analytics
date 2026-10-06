-- Kvant Product Analytics SQL layer

-- Subject performance
SELECT subject, COUNT(*) AS attempts,
       SUM(is_correct) AS correct_answers,
       ROUND(100.0 * AVG(is_correct), 1) AS accuracy_pct
FROM task_attempts
GROUP BY subject
ORDER BY attempts DESC;

-- Weak topics with a minimum-volume guardrail
WITH topic_metrics AS (
  SELECT subject, topic_id, topic, COUNT(*) AS attempts,
         SUM(is_correct) AS correct_answers,
         AVG(is_correct) AS accuracy
  FROM task_attempts
  GROUP BY subject, topic_id, topic
)
SELECT subject, topic_id, topic, attempts, correct_answers,
       ROUND(100.0 * accuracy, 1) AS accuracy_pct
FROM topic_metrics
WHERE attempts >= 10
ORDER BY accuracy ASC, attempts DESC;

-- Difficulty vs accuracy
SELECT difficulty, COUNT(*) AS attempts,
       ROUND(100.0 * AVG(is_correct), 1) AS accuracy_pct
FROM task_attempts
GROUP BY difficulty
ORDER BY difficulty;

-- Daily engagement
SELECT DATE(created_at) AS activity_date,
       COUNT(*) AS attempts,
       SUM(is_correct) AS correct_answers,
       ROUND(100.0 * AVG(is_correct), 1) AS accuracy_pct
FROM task_attempts
GROUP BY DATE(created_at)
ORDER BY activity_date;

-- Rank weak topics within each subject
WITH topic_metrics AS (
  SELECT subject, topic_id, topic, COUNT(*) AS attempts,
         AVG(is_correct) AS accuracy
  FROM task_attempts
  GROUP BY subject, topic_id, topic
),
eligible AS (
  SELECT * FROM topic_metrics WHERE attempts >= 5
)
SELECT subject, topic, attempts,
       ROUND(100.0 * accuracy, 1) AS accuracy_pct,
       RANK() OVER (PARTITION BY subject ORDER BY accuracy) AS weakness_rank
FROM eligible
ORDER BY subject, weakness_rank;