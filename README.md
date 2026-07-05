# CricMetrics Pro — Cricket Analytics Pipeline

An Airflow-orchestrated pipeline that pulls cricket stats from an API, moves
them through a bronze → silver → gold medallion architecture in Postgres, and
serves the result on a live dashboard that queries Postgres directly (no
static exports).

## Architecture

```
                 ┌─────────────────────────┐
   Cricbuzz API  │   get_details_from_      │
   ───────────►   │   cricbuzz               │  downloads cric_data.zip
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │   extract_file_content   │  unzips into file_stores/api_dump/cric_data
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ ingest_data_to_          │  bronze_layer/ingest_data_to_bronze.py
                 │ filesystem                │  raw CSVs → file_stores/bronze_layer/
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ transform_data_from_     │  silver_layer/data_transformations.py
                 │ filesystem                │  cleans + writes base tables to Postgres
                 └────────────┬─────────────┘   (batsmen_*/bowler_*/fielder_* per format)
                              ▼
                 ┌─────────────────────────┐
                 │ refresh_materialized_    │  gold_layer/refresh_materialized_views.py
                 │ views                     │  refreshes/rebuilds every materialized view
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ launch_dashboard          │  starts cricket-dashboard/server.py
                 │                           │  and opens it in the browser
                 └─────────────────────────┘
```

The first four tasks are the existing ETL pipeline (API → filestore → Spark →
Postgres). `refresh_materialized_views` and `launch_dashboard` are appended
to that same DAG (`dags/etl_scheduler.py`) and run after it — nothing about
the original four tasks was changed.

## Data layers

- **Bronze** (`dags/file_stores/bronze_layer/`): raw Cricbuzz CSVs, one folder
  per skill (Batting/Bowling/Fielding) and format (ODI/T20/Test).
- **Silver** (`dags/spark/notebooks/silver_layer/data_transformations.py`):
  PySpark cleans names/countries/dtypes and writes 9 base tables to Postgres
  (`batsmen_odi`, `batsmen_t20`, `batsmen_test`, `bowler_odi`, ..., `fielder_test`)
  via JDBC in overwrite mode — every DAG run fully replaces these tables.
- **Gold** (`dags/spark/notebooks/gold_layer/refresh_materialized_views.py`):
  refreshes 15 materialized views on top of the base tables:
  - `batsmen_stats` / `bowler_stats` / `fielder_stats` — all-formats union per role
  - `{odi,t20,test}_{batsmen,bowler,fielder}_stats_country_wise` — 9 country-wise
    aggregates, one per format × role
  - `player_stats_all_formats_{batsmen,bowler,fielder}` — per-player career
    rollups across formats
  Because Spark overwrites the base tables every run, and a pre-existing
  cleanup step (`erase_stale_data()`) drops a few views via `CASCADE`, this
  script is self-healing: it tries `REFRESH MATERIALIZED VIEW` first and
  falls back to recreating the view from scratch if it's missing.

The full DDL for every table and view lives in `cricket-dashboard/sql/schema.sql`
(extracted from a real `pg_dump` of the `cricket_analyzer` database). Bootstrap
a fresh database with:

```bash
psql -U postgres -d cricket_analyzer -f cricket-dashboard/sql/schema.sql
```

## Dashboard

`cricket-dashboard/` is a small full-stack app with zero extra dependencies
beyond what the pipeline already installs (`psycopg2`, `python-dotenv`):

- **`server.py`** — a stdlib `http.server` app. Serves the static frontend and
  a JSON API (`/api/players`, `/api/rankings`, `/api/country-stats`,
  `/api/countries`) that runs live SQL against Postgres on every request —
  there are no pre-exported JSON/CSV snapshots.
- **`index.html` / `app.js` / `styles.css`** — the frontend. Three tabs:
  - **Overview** / **Compare** — per-player stats and head-to-head comparison,
    backed by `/api/players` (base tables for a single format, or the
    `*_stats` views for "All").
  - **Advanced Analytics** — two sub-tabs:
    - *Player Rankings*, backed by `player_stats_all_formats_*`.
    - *Country Stats*, backed by the `*_stats_country_wise` views, with a
      country dropdown populated from the exact country dictionary in
      `data_transformations.py`'s `get_full_name_and_country()` UDF.

Run it standalone with `python3 cricket-dashboard/server.py [port]` (defaults
to 8000), or let the DAG's `launch_dashboard` task start it automatically.

## Running the pipeline

1. Make sure Postgres is running and `dags/.env` has the right credentials
   (`DATABASE_NAME`, `USER_NAME`, `PASSWORD`, `HOST_NAME`, `PORT`).
2. Trigger the `dag_data` DAG in Airflow.
3. When the DAG finishes, `refresh_materialized_views` will have repopulated
   every materialized view, and `launch_dashboard` will start
   `cricket-dashboard/server.py` (if it isn't already running) and open
   `http://localhost:8000` in your default browser automatically.

## Known environment quirk

`dags/etl_scheduler.py`'s existing tasks reference the absolute path
`/Users/burugula.sasank/airflow/dags/...`, which doesn't match this project's
actual location under `Downloads/airflow/`. That's pre-existing and untouched
here. The two new tasks (`refresh_materialized_views`, `launch_dashboard`)
resolve their paths dynamically from `Path(__file__)` instead, so they work
regardless of where the project root ends up being at runtime.
