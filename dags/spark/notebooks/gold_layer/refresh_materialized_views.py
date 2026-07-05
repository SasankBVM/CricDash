"""
Refresh every materialized view the dashboard depends on.

Runs as the Airflow task right after data_transformations.py has overwritten
the batsmen_*/bowler_*/fielder_* base tables. Materialized views are not
touched by that Spark job, so their contents would otherwise go stale (or, if
a prior run happened to drop one, stay missing) after each DAG run.

Each view is refreshed in dependency order:
  1. batsmen_stats / bowler_stats / fielder_stats        (union of the 3 base tables per role)
  2. *_stats_country_wise views                          (grouped by country, per format)
  3. player_stats_all_formats_*                          (grouped by player, built on top of level 1)

If a view is missing (e.g. dropped by an earlier cleanup step), it is
recreated from the same DDL as cricket-dashboard/sql/schema.sql instead of
just refreshed, so the dashboard never sees a "relation does not exist" error.

Usage: python3 refresh_materialized_views.py
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

DAGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(DAGS_DIR, ".env"))

DB_CONFIG = {
    "host": os.getenv("HOST_NAME", "localhost"),
    "dbname": os.getenv("DATABASE_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "port": os.getenv("PORT", "5432"),
}

# (view_name, CREATE MATERIALIZED VIEW ... AS ... definition, used only if the
# view doesn't exist yet) — kept in the same dependency order it must run in.
VIEW_DEFINITIONS = [
    ("batsmen_stats", """
        CREATE MATERIALIZED VIEW public.batsmen_stats AS
         SELECT full_name, country, years_active, matches_played, innings_played,
                not_outs, "Runs", highest_score, average, hundreds, fifties, ducks, format
           FROM public.batsmen_odi
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                not_outs, "Runs", highest_score, average, hundreds, fifties, ducks, format
           FROM public.batsmen_t20
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                not_outs, "Runs", highest_score, average, hundreds, fifties, ducks, format
           FROM public.batsmen_test
        WITH DATA
    """),
    ("bowler_stats", """
        CREATE MATERIALIZED VIEW public.bowler_stats AS
         SELECT full_name, country, years_active, matches_played, innings_played,
                "Runs", wickets, "BBI", average, economy, strike_rate, five_wicket_hauls, format
           FROM public.bowler_odi
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                "Runs", wickets, "BBI", average, economy, strike_rate, five_wicket_hauls, format
           FROM public.bowler_t20
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                "Runs", wickets, "BBI", average, economy, strike_rate, five_wicket_hauls, format
           FROM public.bowler_test
        WITH DATA
    """),
    ("fielder_stats", """
        CREATE MATERIALIZED VIEW public.fielder_stats AS
         SELECT full_name, country, years_active, matches_played, innings_played,
                dismissals, catches, stumpings, catch_wickets, format
           FROM public.fielder_odi
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                dismissals, catches, stumpings, catch_wickets, format
           FROM public.fielder_t20
        UNION ALL
         SELECT full_name, country, years_active, matches_played, innings_played,
                dismissals, catches, stumpings, catch_wickets, format
           FROM public.fielder_test
        WITH DATA
    """),
    ("odi_batsmen_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.odi_batsmen_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum("Runs") AS total_runs,
                round((avg(average))::numeric, 2) AS average_batting_average,
                round((avg(strike_rate))::numeric, 2) AS average_strike_rate,
                sum(hundreds) AS total_hundreds, sum(fifties) AS total_fifties,
                sum(ducks) AS total_ducks, sum(balls_faced) AS total_balls_faced
           FROM public.batsmen_odi
          GROUP BY country, format
        WITH DATA
    """),
    ("t20_batsmen_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.t20_batsmen_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum("Runs") AS total_runs,
                round((avg(average))::numeric, 2) AS average_batting_average,
                round((avg(strike_rate))::numeric, 2) AS average_strike_rate,
                sum(hundreds) AS total_hundreds, sum(fifties) AS total_fifties,
                sum(ducks) AS total_ducks, sum(balls_faced) AS total_balls_faced
           FROM public.batsmen_t20
          GROUP BY country, format
        WITH DATA
    """),
    ("test_batsmen_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.test_batsmen_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum("Runs") AS total_runs,
                round((avg(average))::numeric, 2) AS average_batting_average,
                round(0.0) AS average_strike_rate,
                sum(hundreds) AS total_hundreds, sum(fifties) AS total_fifties,
                sum(ducks) AS total_ducks, NULL::text AS total_balls_faced
           FROM public.batsmen_test
          GROUP BY country, format
        WITH DATA
    """),
    ("odi_bowler_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.odi_bowler_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(wickets) AS total_wickets, sum("Runs") AS runs_conceded,
                round((avg(average))::numeric, 2) AS average_bowling_average,
                round((avg(strike_rate))::numeric) AS average_strike_rate,
                round((avg(economy))::numeric, 2) AS average_economy,
                sum(four_wicket_hauls) AS total_four_wicket_houls,
                sum(five_wicket_hauls) AS total_five_wicket_hauls
           FROM public.bowler_odi
          GROUP BY country, format
        WITH DATA
    """),
    ("t20_bowler_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.t20_bowler_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(wickets) AS total_wickets, sum("Runs") AS runs_conceded,
                round((avg(average))::numeric, 2) AS average_bowling_average,
                round((avg(strike_rate))::numeric) AS average_strike_rate,
                round((avg(economy))::numeric, 2) AS average_economy,
                sum(four_wicket_hauls) AS total_four_wicket_houls,
                sum(five_wicket_hauls) AS total_five_wicket_hauls
           FROM public.bowler_t20
          GROUP BY country, format
        WITH DATA
    """),
    ("test_bowler_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.test_bowler_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(wickets) AS total_wickets, sum("Runs") AS runs_conceded,
                round((avg(average))::numeric, 2) AS average_bowling_average,
                round((avg(strike_rate))::numeric) AS average_strike_rate,
                round((avg(economy))::numeric, 2) AS average_economy,
                sum(0) AS total_four_wicket_houls,
                sum(five_wicket_hauls) AS total_five_wicket_hauls
           FROM public.bowler_test
          GROUP BY country, format
        WITH DATA
    """),
    ("odi_fielder_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.odi_fielder_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(dismissals) AS total_dismissals, sum(catches) AS total_catches,
                sum(stumpings) AS total_stumpings
           FROM public.fielder_odi
          GROUP BY country, format
        WITH DATA
    """),
    ("t20_fielder_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.t20_fielder_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(dismissals) AS total_dismissals, sum(catches) AS total_catches,
                sum(stumpings) AS total_stumpings
           FROM public.fielder_t20
          GROUP BY country, format
        WITH DATA
    """),
    ("test_fielder_stats_country_wise", """
        CREATE MATERIALIZED VIEW public.test_fielder_stats_country_wise AS
         SELECT country, format, count(full_name) AS number_of_players,
                sum(dismissals) AS total_dismissals, sum(catches) AS total_catches,
                sum(stumpings) AS total_stumpings
           FROM public.fielder_test
          GROUP BY country, format
        WITH DATA
    """),
    ("player_stats_all_formats_batsmen", """
        CREATE MATERIALIZED VIEW public.player_stats_all_formats_batsmen AS
         SELECT full_name, country, count(format) AS formats_played,
                array_agg(format) AS format_list, max(years_active) AS max_career_span,
                sum("Runs") AS total_runs, sum(matches_played) AS total_matches,
                sum(not_outs) AS total_not_outs, sum(hundreds) AS total_centuries,
                sum(fifties) AS total_fifties, sum(ducks) AS total_ducks,
                round(((sum(CASE WHEN average > 0 THEN average ELSE 0 END)
                      / NULLIF(count(CASE WHEN average > 0 THEN 1 ELSE NULL END), 0))
                      )::numeric, 2) AS total_average
           FROM public.batsmen_stats
          GROUP BY full_name, country
          ORDER BY (sum(matches_played)) DESC
        WITH DATA
    """),
    ("player_stats_all_formats_bowler", """
        CREATE MATERIALIZED VIEW public.player_stats_all_formats_bowler AS
         SELECT full_name, country, count(format) AS formats_played,
                array_agg(format) AS format_list, sum(matches_played) AS total_matches,
                sum(wickets) AS total_wickets, sum("Runs") AS total_runs_conceded,
                round(((sum(CASE WHEN average > 0 THEN average ELSE 0 END)
                      / NULLIF(count(CASE WHEN average > 0 THEN 1 ELSE NULL END), 0))
                      )::numeric, 2) AS average_bowling_average,
                round(((sum(CASE WHEN economy > 0 THEN economy ELSE 0 END)
                      / NULLIF(count(CASE WHEN economy > 0 THEN 1 ELSE NULL END), 0))
                      )::numeric, 2) AS average_bowling_economy,
                round(((sum(CASE WHEN strike_rate > 0 THEN strike_rate ELSE 0 END)
                      / NULLIF(count(CASE WHEN strike_rate > 0 THEN 1 ELSE NULL END), 0))
                      )::numeric, 2) AS average_bowling_strike_rate
           FROM public.bowler_stats
          GROUP BY full_name, country
          ORDER BY full_name, country
        WITH DATA
    """),
    ("player_stats_all_formats_fielder", """
        CREATE MATERIALIZED VIEW public.player_stats_all_formats_fielder AS
         SELECT full_name, country, count(format) AS formats_played,
                array_agg(format) AS format_list, sum(catches) AS total_catches,
                sum(catch_wickets) AS total_wicket_keeper_catches,
                sum(stumpings) AS total_stumpings
           FROM public.fielder_stats
          GROUP BY full_name, country
          ORDER BY full_name, country
        WITH DATA
    """),
]


def refresh_all():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True  # each DDL statement stands on its own
    cursor = conn.cursor()

    try:
        for view_name, create_ddl in VIEW_DEFINITIONS:
            try:
                cursor.execute(f"REFRESH MATERIALIZED VIEW public.{view_name}")
                print(f"Refreshed {view_name}")
            except psycopg2.errors.UndefinedTable:
                print(f"{view_name} missing, recreating from DDL")
                cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS public.{view_name} CASCADE")
                cursor.execute(create_ddl)
                print(f"Created {view_name}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        refresh_all()
        print("All materialized views are up to date.")
    except Exception as exc:
        print(f"Failed to refresh materialized views: {exc}")
        sys.exit(1)
