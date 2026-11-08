# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Load races and runners into Delta tables
# MAGIC Pick a source. All options end up as two tables in `workspace.horse_racing`:
# MAGIC * `races`   - one row per race
# MAGIC * `runners` - one row per horse per race (with SP odds and finishing position)

# COMMAND ----------
CATALOG, SCHEMA = "workspace", "horse_racing"
SOURCE = "demo"     # "demo" (synthetic) | "csv" (file in a Volume)

# csv settings: one row per runner, race fields repeated on every row (typical for public datasets)
CSV_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/raw/races.csv"
# map YOUR csv column names -> our names (left = your file, right = ours)
COLMAP = {
    "date": "race_date", "course": "track", "race_number": "race_no", "distance": "distance_m",
    "surface": "surface", "going": "going", "prize": "purse",
    "horse_name": "horse", "jockey_name": "jockey", "trainer_name": "trainer",
    "draw": "draw", "starting_price": "sp_decimal", "position": "finish_pos",
}

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.raw")

# COMMAND ----------
from pyspark.sql import functions as F

if SOURCE == "demo":
    import sys, os
    sys.path.append(os.getcwd())          # so demo_data.py next to this notebook is importable
    from demo_data import make_demo
    races_pdf, runners_pdf = make_demo()
    races = spark.createDataFrame(races_pdf)
    runners = spark.createDataFrame(runners_pdf)

elif SOURCE == "csv":
    raw = spark.read.option("header", True).option("inferSchema", True).csv(CSV_PATH)
    for old, new in COLMAP.items():
        raw = raw.withColumnRenamed(old, new)
    raw = (raw
        .withColumn("race_date", F.to_date("race_date"))
        .withColumn("race_id", F.sha1(F.concat_ws("|", "race_date", "track", "race_no")))
        .withColumn("is_synthetic", F.lit(False)))
    race_cols = ["race_id", "race_date", "track", "race_no", "distance_m", "surface", "going", "purse", "is_synthetic"]
    run_cols = ["race_id", "horse", "jockey", "trainer", "draw", "sp_decimal", "finish_pos"]
    races = raw.select(*race_cols).dropDuplicates(["race_id"])
    # drop runners that did not finish with a numeric position (DNF, PU, etc.)
    runners = (raw.select(*run_cols)
        .withColumn("finish_pos", F.col("finish_pos").cast("int"))
        .withColumn("sp_decimal", F.col("sp_decimal").cast("double"))
        .where("finish_pos IS NOT NULL AND sp_decimal > 1"))
else:
    raise ValueError("SOURCE must be 'demo' or 'csv'")

races.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.races")
runners.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.runners")
print(spark.table(f"{CATALOG}.{SCHEMA}.races").count(), "races;",
      spark.table(f"{CATALOG}.{SCHEMA}.runners").count(), "runners")

# COMMAND ----------
# MAGIC %md
# MAGIC Odds must be **decimal** (e.g. 4.50 means a $1 winning bet returns $4.50). Convert fractional odds (7/2) first: `1 + 7/2`.
