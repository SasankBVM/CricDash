-- ============================================================================
-- Cricket Analyzer — PostgreSQL schema
-- ============================================================================
-- Source of truth for the tables Spark (silver layer) writes into and the
-- materialized views the dashboard reads from. Extracted from a real
-- `pg_dump` of the `cricket_analyzer` database.
--
-- The base tables (batsmen_*/bowler_*/fielder_*) are recreated by
-- dags/spark/notebooks/silver_layer/data_transformations.py on every DAG run
-- (Spark JDBC "overwrite" mode), so the CREATE TABLE statements below only
-- matter for a first-time bootstrap of an empty database.
--
-- The materialized views are NOT touched by Spark. They are (re)created and
-- refreshed by dags/spark/notebooks/gold_layer/refresh_materialized_views.py
-- after every ETL run, using the exact same DDL as below.
--
-- Run once against a fresh database with:
--   psql -U postgres -d cricket_analyzer -f cricket-dashboard/sql/schema.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Base tables (one per role x format)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.batsmen_odi (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    not_outs integer,
    "Runs" integer,
    highest_score integer,
    average real,
    balls_faced integer,
    strike_rate real,
    hundreds integer,
    fifties integer,
    ducks integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.batsmen_t20 (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    not_outs integer,
    "Runs" integer,
    highest_score integer,
    average real,
    balls_faced integer,
    strike_rate real,
    hundreds integer,
    fifties integer,
    ducks integer,
    number_of_fours integer,
    number_of_sixes integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.batsmen_test (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    not_outs integer,
    "Runs" integer,
    highest_score integer,
    average real,
    hundreds integer,
    fifties integer,
    ducks integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.bowler_odi (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    "Balls" integer,
    "Runs" integer,
    wickets integer,
    "BBI" text,
    average real,
    economy real,
    strike_rate real,
    four_wicket_hauls integer,
    five_wicket_hauls integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.bowler_t20 (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    "Overs" integer,
    number_of_maidens integer,
    "Runs" integer,
    wickets integer,
    "BBI" text,
    average real,
    economy real,
    strike_rate real,
    four_wicket_hauls integer,
    five_wicket_hauls integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.bowler_test (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    "Balls" integer,
    "Runs" integer,
    wickets integer,
    "BBI" text,
    "BBM" text,
    average real,
    economy real,
    strike_rate real,
    five_wicket_hauls integer,
    "10" integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.fielder_odi (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    dismissals integer,
    catches integer,
    stumpings integer,
    catch_wickets integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.fielder_t20 (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    dismissals integer,
    catches integer,
    stumpings integer,
    catch_wickets integer,
    format text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.fielder_test (
    full_name text,
    country text,
    years_active integer,
    matches_played integer,
    innings_played integer,
    dismissals integer,
    catches integer,
    stumpings integer,
    catch_wickets integer,
    format text NOT NULL
);

-- ----------------------------------------------------------------------------
-- Level 1 materialized views — combined "all formats" role views
-- (depend only on the base tables above)
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS public.batsmen_stats AS
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
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.bowler_stats AS
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
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.fielder_stats AS
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
  WITH NO DATA;

-- ----------------------------------------------------------------------------
-- Level 1 materialized views — country-wise, per format
-- (depend only on the base tables above)
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS public.odi_batsmen_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum("Runs") AS total_runs,
        round((avg(average))::numeric, 2) AS average_batting_average,
        round((avg(strike_rate))::numeric, 2) AS average_strike_rate,
        sum(hundreds) AS total_hundreds,
        sum(fifties) AS total_fifties,
        sum(ducks) AS total_ducks,
        sum(balls_faced) AS total_balls_faced
   FROM public.batsmen_odi
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.t20_batsmen_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum("Runs") AS total_runs,
        round((avg(average))::numeric, 2) AS average_batting_average,
        round((avg(strike_rate))::numeric, 2) AS average_strike_rate,
        sum(hundreds) AS total_hundreds,
        sum(fifties) AS total_fifties,
        sum(ducks) AS total_ducks,
        sum(balls_faced) AS total_balls_faced
   FROM public.batsmen_t20
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.test_batsmen_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum("Runs") AS total_runs,
        round((avg(average))::numeric, 2) AS average_batting_average,
        round(0.0) AS average_strike_rate,
        sum(hundreds) AS total_hundreds,
        sum(fifties) AS total_fifties,
        sum(ducks) AS total_ducks,
        NULL::text AS total_balls_faced
   FROM public.batsmen_test
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.odi_bowler_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(wickets) AS total_wickets,
        sum("Runs") AS runs_conceded,
        round((avg(average))::numeric, 2) AS average_bowling_average,
        round((avg(strike_rate))::numeric) AS average_strike_rate,
        round((avg(economy))::numeric, 2) AS average_economy,
        sum(four_wicket_hauls) AS total_four_wicket_houls,
        sum(five_wicket_hauls) AS total_five_wicket_hauls
   FROM public.bowler_odi
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.t20_bowler_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(wickets) AS total_wickets,
        sum("Runs") AS runs_conceded,
        round((avg(average))::numeric, 2) AS average_bowling_average,
        round((avg(strike_rate))::numeric) AS average_strike_rate,
        round((avg(economy))::numeric, 2) AS average_economy,
        sum(four_wicket_hauls) AS total_four_wicket_houls,
        sum(five_wicket_hauls) AS total_five_wicket_hauls
   FROM public.bowler_t20
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.test_bowler_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(wickets) AS total_wickets,
        sum("Runs") AS runs_conceded,
        round((avg(average))::numeric, 2) AS average_bowling_average,
        round((avg(strike_rate))::numeric) AS average_strike_rate,
        round((avg(economy))::numeric, 2) AS average_economy,
        sum(0) AS total_four_wicket_houls,
        sum(five_wicket_hauls) AS total_five_wicket_hauls
   FROM public.bowler_test
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.odi_fielder_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(dismissals) AS total_dismissals,
        sum(catches) AS total_catches,
        sum(stumpings) AS total_stumpings
   FROM public.fielder_odi
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.t20_fielder_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(dismissals) AS total_dismissals,
        sum(catches) AS total_catches,
        sum(stumpings) AS total_stumpings
   FROM public.fielder_t20
  GROUP BY country, format
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.test_fielder_stats_country_wise AS
 SELECT country, format,
        count(full_name) AS number_of_players,
        sum(dismissals) AS total_dismissals,
        sum(catches) AS total_catches,
        sum(stumpings) AS total_stumpings
   FROM public.fielder_test
  GROUP BY country, format
  WITH NO DATA;

-- ----------------------------------------------------------------------------
-- Level 2 materialized views — per-player, across all formats
-- (depend on the Level 1 combined views above)
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS public.player_stats_all_formats_batsmen AS
 SELECT full_name, country,
        count(format) AS formats_played,
        array_agg(format) AS format_list,
        max(years_active) AS max_career_span,
        sum("Runs") AS total_runs,
        sum(matches_played) AS total_matches,
        sum(not_outs) AS total_not_outs,
        sum(hundreds) AS total_centuries,
        sum(fifties) AS total_fifties,
        sum(ducks) AS total_ducks,
        round(((sum(CASE WHEN average > 0 THEN average ELSE 0 END)
              / NULLIF(count(CASE WHEN average > 0 THEN 1 ELSE NULL END), 0))
              )::numeric, 2) AS total_average
   FROM public.batsmen_stats
  GROUP BY full_name, country
  ORDER BY (sum(matches_played)) DESC
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.player_stats_all_formats_bowler AS
 SELECT full_name, country,
        count(format) AS formats_played,
        array_agg(format) AS format_list,
        sum(matches_played) AS total_matches,
        sum(wickets) AS total_wickets,
        sum("Runs") AS total_runs_conceded,
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
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.player_stats_all_formats_fielder AS
 SELECT full_name, country,
        count(format) AS formats_played,
        array_agg(format) AS format_list,
        sum(catches) AS total_catches,
        sum(catch_wickets) AS total_wicket_keeper_catches,
        sum(stumpings) AS total_stumpings
   FROM public.fielder_stats
  GROUP BY full_name, country
  ORDER BY full_name, country
  WITH NO DATA;
