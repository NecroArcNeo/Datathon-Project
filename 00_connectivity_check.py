# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Can this workspace reach the internet?
# MAGIC Databricks **Free Edition only allows outbound access to a short list of trusted domains**, so scraping or calling
# MAGIC a racing API from a notebook may be blocked. Run this first and edit `URLS` to the hosts you care about.

# COMMAND ----------
import requests

URLS = [
    "https://pypi.org/simple/",            # package index (normally allowed)
    "https://raw.githubusercontent.com/",  # GitHub raw files (often allowed)
    "https://example.com/",                # replace with your racing data/API host
]
for u in URLS:
    try:
        r = requests.get(u, timeout=10)
        print(f"OK    {r.status_code}  {u}")
    except Exception as e:
        print(f"BLOCKED/FAILED  {u}  ->  {type(e).__name__}: {str(e)[:120]}")

# COMMAND ----------
# MAGIC %md
# MAGIC **If your data host fails:** download the CSV/JSON on your own computer and upload it to a Unity Catalog Volume
# MAGIC (Catalog > workspace > horse_racing > raw > Upload). Then use `SOURCE = "csv"` in notebook 01.
