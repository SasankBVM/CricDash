"""
CricMetrics Pro dashboard backend.

Serves the static frontend (index.html/app.js/styles.css/cover.png) and a
small JSON API that runs live queries against the cricket_analyzer Postgres
database — no CSV/JSON exports involved. Every request re-queries Postgres,
so the UI always reflects whatever the latest DAG run wrote to the base
tables and materialized views.

Endpoints:
  GET /api/health
  GET /api/players?role=batsmen|bowler|fielder&format=ODI|T20|Test|All
  GET /api/rankings?role=batsmen|bowler|fielder
  GET /api/countries
  GET /api/country-stats?role=batsmen|bowler|fielder&format=ODI|T20|Test|All[&country=<name>]

Usage: python3 server.py [port]   (defaults to 8000)
"""

import json
import os
import sys
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT.parent / "dags" / ".env")

DB_CONFIG = {
    "host": os.getenv("HOST_NAME", "localhost"),
    "dbname": os.getenv("DATABASE_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "port": os.getenv("PORT", "5432"),
}

# Canonical country names, matching dags/spark/notebooks/silver_layer/data_transformations.py's
# get_full_name_and_country() dictionary values exactly (deduplicated, same spelling).
COUNTRIES = sorted({
    "India", "Bermuda", "Sri Lanka", "New Zealand", "West Indies", "Bangladesh",
    "Zimbabwe", "Australia", "Afganisthan", "South Africa", "England", "Ireland",
    "Papua New Guinea", "Kenya", "Pakistan", "Namibia", "United Arab Emirates",
    "HongKonng", "Netherlands", "Scotland", "Canada", "Nepal",
})

ROLES = {"batsmen", "bowler", "fielder"}
FORMATS = {"ODI", "T20", "Test"}

# Per role/format SELECT lists, aliased so every response uses the same field
# names regardless of which base table/format backs it.
PLAYER_QUERIES = {
    "batsmen": {
        "ODI": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   not_outs, "Runs" AS runs, highest_score, average, balls_faced,
                   strike_rate, hundreds, fifties, ducks, format
              FROM public.batsmen_odi
        """,
        "T20": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   not_outs, "Runs" AS runs, highest_score, average, balls_faced,
                   strike_rate, hundreds, fifties, ducks,
                   number_of_fours AS fours, number_of_sixes AS sixes, format
              FROM public.batsmen_t20
        """,
        "Test": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   not_outs, "Runs" AS runs, highest_score, average,
                   hundreds, fifties, ducks, format
              FROM public.batsmen_test
        """,
        "All": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   not_outs, "Runs" AS runs, highest_score, average,
                   hundreds, fifties, ducks, format
              FROM public.batsmen_stats
        """,
    },
    "bowler": {
        "ODI": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   "Balls" AS balls, "Runs" AS runs_conceded, wickets, "BBI" AS best_innings,
                   average, economy, strike_rate, four_wicket_hauls, five_wicket_hauls, format
              FROM public.bowler_odi
        """,
        "T20": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   "Overs" AS balls, number_of_maidens AS maidens, "Runs" AS runs_conceded,
                   wickets, "BBI" AS best_innings, average, economy, strike_rate,
                   four_wicket_hauls, five_wicket_hauls, format
              FROM public.bowler_t20
        """,
        "Test": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   "Balls" AS balls, "Runs" AS runs_conceded, wickets, "BBI" AS best_innings,
                   "BBM" AS best_match, average, economy, strike_rate,
                   five_wicket_hauls, "10" AS ten_wicket_hauls, format
              FROM public.bowler_test
        """,
        "All": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   "Runs" AS runs_conceded, wickets, "BBI" AS best_innings,
                   average, economy, strike_rate, five_wicket_hauls, format
              FROM public.bowler_stats
        """,
    },
    "fielder": {
        "ODI": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   dismissals, catches, stumpings, catch_wickets, format
              FROM public.fielder_odi
        """,
        "T20": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   dismissals, catches, stumpings, catch_wickets, format
              FROM public.fielder_t20
        """,
        "Test": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   dismissals, catches, stumpings, catch_wickets, format
              FROM public.fielder_test
        """,
        "All": """
            SELECT full_name, country, years_active, matches_played, innings_played,
                   dismissals, catches, stumpings, catch_wickets, format
              FROM public.fielder_stats
        """,
    },
}

RANKINGS_QUERIES = {
    "batsmen": """
        SELECT * FROM public.player_stats_all_formats_batsmen
         ORDER BY total_runs DESC, total_matches DESC
    """,
    "bowler": """
        SELECT * FROM public.player_stats_all_formats_bowler
         ORDER BY total_wickets DESC, total_matches DESC
    """,
    "fielder": """
        SELECT * FROM public.player_stats_all_formats_fielder
         ORDER BY total_catches DESC, total_wicket_keeper_catches DESC, total_stumpings DESC
    """,
}

# Country-wise queries per role/format. "All" sums across the three per-format
# materialized views (explicit column lists so UNION ALL never hits a type
# mismatch, e.g. test_batsmen_stats_country_wise's NULL::text balls-faced column).
COUNTRY_QUERIES = {
    "batsmen": {
        "ODI": "SELECT country, format, number_of_players, total_runs, average_batting_average, "
               "average_strike_rate, total_hundreds, total_fifties, total_ducks "
               "FROM public.odi_batsmen_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_runs, average_batting_average, "
               "average_strike_rate, total_hundreds, total_fifties, total_ducks "
               "FROM public.t20_batsmen_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_runs, average_batting_average, "
                "average_strike_rate, total_hundreds, total_fifties, total_ducks "
                "FROM public.test_batsmen_stats_country_wise",
        "All": """
            SELECT country, 'All' AS format,
                   SUM(number_of_players) AS number_of_players,
                   SUM(total_runs) AS total_runs,
                   ROUND(AVG(average_batting_average)::numeric, 2) AS average_batting_average,
                   ROUND(AVG(average_strike_rate)::numeric, 2) AS average_strike_rate,
                   SUM(total_hundreds) AS total_hundreds,
                   SUM(total_fifties) AS total_fifties,
                   SUM(total_ducks) AS total_ducks
              FROM (
                SELECT country, number_of_players, total_runs, average_batting_average,
                       average_strike_rate, total_hundreds, total_fifties, total_ducks
                  FROM public.odi_batsmen_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_runs, average_batting_average,
                       average_strike_rate, total_hundreds, total_fifties, total_ducks
                  FROM public.t20_batsmen_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_runs, average_batting_average,
                       average_strike_rate, total_hundreds, total_fifties, total_ducks
                  FROM public.test_batsmen_stats_country_wise
              ) combined
             GROUP BY country
        """,
    },
    "bowler": {
        "ODI": "SELECT country, format, number_of_players, total_wickets, runs_conceded, "
               "average_bowling_average, average_strike_rate, average_economy, "
               "total_four_wicket_houls, total_five_wicket_hauls "
               "FROM public.odi_bowler_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_wickets, runs_conceded, "
               "average_bowling_average, average_strike_rate, average_economy, "
               "total_four_wicket_houls, total_five_wicket_hauls "
               "FROM public.t20_bowler_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_wickets, runs_conceded, "
                "average_bowling_average, average_strike_rate, average_economy, "
                "total_four_wicket_houls, total_five_wicket_hauls "
                "FROM public.test_bowler_stats_country_wise",
        "All": """
            SELECT country, 'All' AS format,
                   SUM(number_of_players) AS number_of_players,
                   SUM(total_wickets) AS total_wickets,
                   SUM(runs_conceded) AS runs_conceded,
                   ROUND(AVG(average_bowling_average)::numeric, 2) AS average_bowling_average,
                   ROUND(AVG(average_strike_rate)::numeric, 2) AS average_strike_rate,
                   ROUND(AVG(average_economy)::numeric, 2) AS average_economy,
                   SUM(total_four_wicket_houls) AS total_four_wicket_houls,
                   SUM(total_five_wicket_hauls) AS total_five_wicket_hauls
              FROM (
                SELECT country, number_of_players, total_wickets, runs_conceded,
                       average_bowling_average, average_strike_rate, average_economy,
                       total_four_wicket_houls, total_five_wicket_hauls
                  FROM public.odi_bowler_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_wickets, runs_conceded,
                       average_bowling_average, average_strike_rate, average_economy,
                       total_four_wicket_houls, total_five_wicket_hauls
                  FROM public.t20_bowler_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_wickets, runs_conceded,
                       average_bowling_average, average_strike_rate, average_economy,
                       total_four_wicket_houls, total_five_wicket_hauls
                  FROM public.test_bowler_stats_country_wise
              ) combined
             GROUP BY country
        """,
    },
    "fielder": {
        "ODI": "SELECT country, format, number_of_players, total_dismissals, total_catches, "
               "total_stumpings FROM public.odi_fielder_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_dismissals, total_catches, "
               "total_stumpings FROM public.t20_fielder_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_dismissals, total_catches, "
                "total_stumpings FROM public.test_fielder_stats_country_wise",
        "All": """
            SELECT country, 'All' AS format,
                   SUM(number_of_players) AS number_of_players,
                   SUM(total_dismissals) AS total_dismissals,
                   SUM(total_catches) AS total_catches,
                   SUM(total_stumpings) AS total_stumpings
              FROM (
                SELECT country, number_of_players, total_dismissals, total_catches, total_stumpings
                  FROM public.odi_fielder_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_dismissals, total_catches, total_stumpings
                  FROM public.t20_fielder_stats_country_wise
                UNION ALL
                SELECT country, number_of_players, total_dismissals, total_catches, total_stumpings
                  FROM public.test_fielder_stats_country_wise
              ) combined
             GROUP BY country
        """,
    },
}


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_query(sql, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql, params or ())
            return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format_str, *args):
        sys.stderr.write(f"[server] {self.address_string()} {format_str % args}\n")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api(parsed.path, parse_qs(parsed.query))
        else:
            self.handle_static(parsed.path)

    def handle_api(self, path, query):
        try:
            if path == "/api/health":
                return self.send_json({"status": "ok"})

            if path == "/api/countries":
                return self.send_json(COUNTRIES)

            if path == "/api/players":
                role = query.get("role", [""])[0]
                fmt = query.get("format", ["All"])[0]
                if role not in ROLES or fmt not in (FORMATS | {"All"}):
                    return self.send_json({"error": "invalid role or format"}, status=400)
                return self.send_json(run_query(PLAYER_QUERIES[role][fmt]))

            if path == "/api/rankings":
                role = query.get("role", [""])[0]
                if role not in ROLES:
                    return self.send_json({"error": "invalid role"}, status=400)
                return self.send_json(run_query(RANKINGS_QUERIES[role]))

            if path == "/api/country-stats":
                role = query.get("role", [""])[0]
                fmt = query.get("format", ["All"])[0]
                country = query.get("country", [""])[0]
                if role not in ROLES or fmt not in (FORMATS | {"All"}):
                    return self.send_json({"error": "invalid role or format"}, status=400)
                sql = COUNTRY_QUERIES[role][fmt]
                if country:
                    sql = f"SELECT * FROM ({sql}) filtered WHERE country = %s"
                    return self.send_json(run_query(sql, (country,)))
                return self.send_json(run_query(sql))

            self.send_json({"error": "not found"}, status=404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def handle_static(self, path):
        if path == "/":
            path = "/index.html"
        file_path = (PROJECT_ROOT / path.lstrip("/")).resolve()
        if PROJECT_ROOT not in file_path.parents and file_path != PROJECT_ROOT:
            return self.send_error(403)
        if not file_path.is_file():
            return self.send_error(404)

        content_types = {
            ".html": "text/html", ".js": "application/javascript",
            ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg",
            ".svg": "image/svg+xml", ".json": "application/json",
        }
        content_type = content_types.get(file_path.suffix, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, default=decimal_to_float).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def serve(port=8000):
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardRequestHandler)
    print(f"CricMetrics Pro dashboard serving on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    serve(port)
