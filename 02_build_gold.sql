-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 - Gold tables for the dashboard
-- MAGIC Flat-$1 ROI on a runner = (sp_decimal - 1) if it won, else -1.

-- COMMAND ----------
USE CATALOG workspace;
USE SCHEMA horse_racing;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_runner_results AS
SELECT
  ru.*, ra.race_date, ra.track, ra.race_no, ra.distance_m, ra.surface, ra.going, ra.purse,
  COUNT(*) OVER (PARTITION BY ru.race_id) AS field_size,
  ROW_NUMBER() OVER (PARTITION BY ru.race_id ORDER BY ru.sp_decimal ASC, ru.draw) AS odds_rank,
  1.0 / ru.sp_decimal AS implied_prob,
  CASE WHEN ru.finish_pos = 1 THEN 1 ELSE 0 END AS is_winner,
  CASE WHEN ru.finish_pos = 1 THEN ru.sp_decimal - 1 ELSE -1 END AS flat_profit
FROM runners ru JOIN races ra USING (race_id);

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_track_summary AS
SELECT track,
       COUNT(DISTINCT race_id) AS races,
       ROUND(AVG(field_size), 1) AS avg_field_size,
       ROUND(AVG(CASE WHEN odds_rank = 1 THEN is_winner END), 3) AS favorite_win_rate,
       ROUND(AVG(CASE WHEN odds_rank = 1 THEN flat_profit END), 3) AS favorite_roi
FROM gold_runner_results GROUP BY track;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_odds_calibration AS
SELECT
  CASE WHEN sp_decimal < 2 THEN '1) under 2.0'
       WHEN sp_decimal < 4 THEN '2) 2.0-3.9'
       WHEN sp_decimal < 8 THEN '3) 4.0-7.9'
       WHEN sp_decimal < 15 THEN '4) 8.0-14.9'
       ELSE '5) 15+' END AS odds_bucket,
  COUNT(*) AS runners,
  ROUND(AVG(implied_prob), 3) AS avg_implied_prob,
  ROUND(AVG(is_winner), 3) AS actual_win_rate,
  ROUND(AVG(flat_profit), 3) AS flat_roi
FROM gold_runner_results GROUP BY 1;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_jockey_leaderboard AS
SELECT jockey, COUNT(*) AS rides, SUM(is_winner) AS wins,
       ROUND(AVG(is_winner), 3) AS win_rate,
       ROUND(AVG(flat_profit), 3) AS flat_roi
FROM gold_runner_results GROUP BY jockey HAVING COUNT(*) >= 30;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_trainer_leaderboard AS
SELECT trainer, COUNT(*) AS runs, SUM(is_winner) AS wins,
       ROUND(AVG(is_winner), 3) AS win_rate,
       ROUND(AVG(flat_profit), 3) AS flat_roi
FROM gold_runner_results GROUP BY trainer HAVING COUNT(*) >= 30;

-- COMMAND ----------
-- Draw bias: win rate vs what a fair draw would give (1 / field size)
CREATE OR REPLACE TABLE gold_draw_bias AS
SELECT track, draw, COUNT(*) AS runs,
       ROUND(AVG(is_winner), 3) AS win_rate,
       ROUND(AVG(1.0 / field_size), 3) AS expected_win_rate,
       ROUND(AVG(is_winner) - AVG(1.0 / field_size), 3) AS edge
FROM gold_runner_results WHERE draw <= 12 GROUP BY track, draw HAVING COUNT(*) >= 20;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_going_summary AS
SELECT surface, going, COUNT(DISTINCT race_id) AS races,
       ROUND(AVG(CASE WHEN odds_rank = 1 THEN is_winner END), 3) AS favorite_win_rate
FROM gold_runner_results GROUP BY surface, going;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_monthly_trend AS
SELECT DATE_TRUNC('month', race_date) AS month,
       COUNT(DISTINCT race_id) AS races,
       ROUND(AVG(field_size), 1) AS avg_field_size,
       ROUND(AVG(CASE WHEN odds_rank = 1 THEN is_winner END), 3) AS favorite_win_rate
FROM gold_runner_results GROUP BY 1;

-- COMMAND ----------
CREATE OR REPLACE TABLE gold_top_horses AS
SELECT horse, COUNT(*) AS runs, SUM(is_winner) AS wins,
       ROUND(AVG(finish_pos), 2) AS avg_finish, MAX(race_date) AS last_run
FROM gold_runner_results GROUP BY horse HAVING COUNT(*) >= 5;
