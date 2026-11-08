# Horse racing analytics on Databricks (Free Edition)

Pipeline: **load data -> Delta tables (races, runners) -> gold tables (SQL) -> AI/BI dashboard**.

## Files
| File | What it does |
|---|---|
| `00_connectivity_check.py` | Tests whether your workspace can reach a site (Free Edition limits outbound access) |
| `01_load_data.py` | Loads `races` and `runners`. `SOURCE = "demo"` (synthetic) or `"csv"` (file in a Volume) |
| `demo_data.py` | Synthetic data generator, so everything runs with no data source (rows flagged `is_synthetic`) |
| `02_build_gold.sql` | Builds 9 gold tables the dashboard reads |

## Setup
1. Sign up for Databricks Free Edition and open the workspace.
2. Workspace > Create > Git folder (or upload all four files into one workspace folder, keep them together).
3. Run `00_connectivity_check.py`, then `01_load_data.py` (demo first), then `02_build_gold.sql`.
4. Create the dashboard: Dashboards > Create dashboard > Data tab > add each `workspace.horse_racing.gold_*` table as a dataset.

## Dashboard layout (suggested)
- **Filters:** track, surface, date range (add via Filters, bound to the datasets that have those columns)
- **Row 1 (counters):** total races, favorite win rate (`gold_track_summary`)
- **Row 2:** bar - favorite win rate by track; line - monthly races and favorite win rate (`gold_monthly_trend`)
- **Row 3:** calibration bar - implied probability vs actual win rate per odds bucket (`gold_odds_calibration`); table - going summary
- **Row 4:** jockey and trainer leaderboards (tables, sort by win_rate); top horses table
- **Row 5:** draw-bias heatmap: x = draw, y = track, color = `edge` (`gold_draw_bias`)

## Real data
- Free Edition may block your data host. If the check fails, download the data on your computer, upload it to the `raw` Volume, and use `SOURCE = "csv"` with your column names in `COLMAP`.
- Many sites forbid scraping in their terms. Check the terms and robots.txt, or prefer an API or a public dataset.
- Odds must be decimal. Convert fractional odds first.

## Notes
- Gold SQL was tested locally on DuckDB with the demo data (every race has one winner; tables build). The Spark `csv` loader and the notebooks were not run on Databricks.
- Free Edition limits: serverless compute only, one 2X-Small SQL warehouse, apps stop after 24h, daily fair-use quota.
