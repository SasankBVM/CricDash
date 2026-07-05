# SQL Queries Guide for Cricket Analytics Project

This guide explains where to write and manage SQL queries in this cricket analytics project.

## Overview

The project uses PostgreSQL as the database and has SQL queries in two main locations:

## 1. Schema Definition & Materialized Views
**Location:** [`cricket-dashboard/sql/schema.sql`](sql/schema.sql)

This file contains:
- **Base table definitions** (lines 25-172): Tables for batting, bowling, and fielding stats across ODI, T20, and Test formats
- **Level 1 materialized views** (lines 179-338): Combined views and country-wise statistics per format
- **Level 2 materialized views** (lines 345-395): Player statistics aggregated across all formats

### When to edit this file:
- Adding new tables to the database
- Creating new materialized views
- Modifying existing view definitions
- Adding new aggregations or statistics

### Example: Adding a new materialized view
```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS public.your_new_view AS
 SELECT column1, column2, 
        SUM(metric) AS total_metric
   FROM public.source_table
  GROUP BY column1, column2
  WITH NO DATA;
```

## 2. API Query Definitions
**Location:** [`cricket-dashboard/server.py`](server.py)

This file contains Python dictionaries that define SQL queries for the API endpoints:

### Query Dictionaries:

#### `PLAYER_QUERIES` (lines 56-134)
Queries for fetching individual player statistics by role and format.

**Structure:**
```python
PLAYER_QUERIES = {
    "batsmen": {
        "ODI": "SELECT ... FROM public.batsmen_odi",
        "T20": "SELECT ... FROM public.batsmen_t20",
        "Test": "SELECT ... FROM public.batsmen_test",
        "All": "SELECT ... FROM public.batsmen_stats"
    },
    # Similar for "bowler" and "fielder"
}
```

#### `RANKINGS_QUERIES` (lines 136-140)
Queries for all-format player rankings.

**Structure:**
```python
RANKINGS_QUERIES = {
    "batsmen": "SELECT * FROM public.player_stats_all_formats_batsmen",
    "bowler": "SELECT * FROM public.player_stats_all_formats_bowler",
    "fielder": "SELECT * FROM public.player_stats_all_formats_fielder",
}
```

#### `COUNTRY_QUERIES` (lines 145-249)
Queries for country-wise statistics by role and format.

**Structure:**
```python
COUNTRY_QUERIES = {
    "batsmen": {
        "ODI": "SELECT ... FROM public.odi_batsmen_stats_country_wise",
        "T20": "SELECT ... FROM public.t20_batsmen_stats_country_wise",
        "Test": "SELECT ... FROM public.test_batsmen_stats_country_wise",
        "All": "SELECT ... (UNION ALL query combining all formats)"
    },
    # Similar for "bowler" and "fielder"
}
```

### When to edit server.py queries:
- Adding new API endpoints
- Modifying which columns are returned to the frontend
- Changing how data is aggregated for the "All" format
- Adding filters or WHERE clauses to existing queries

### Example: Adding a new metric to player queries
```python
PLAYER_QUERIES = {
    "batsmen": {
        "ODI": """
            SELECT full_name, country, years_active, matches_played,
                   "Runs" AS runs, average, strike_rate,
                   your_new_metric,  -- Add your new column here
                   format
              FROM public.batsmen_odi
        """,
        # Update other formats similarly
    }
}
```

## 3. Data Transformation Queries
**Location:** [`dags/spark/notebooks/silver_layer/data_transformations.py`](../dags/spark/notebooks/silver_layer/data_transformations.py)

This file contains Spark SQL queries used during the ETL process to transform data from bronze to silver layer.

### When to edit this file:
- Modifying data transformations during ETL
- Adding new calculated fields
- Changing data cleaning logic

## 4. Gold Layer Materialized View Refresh
**Location:** [`dags/spark/notebooks/gold_layer/refresh_materialized_views.py`](../dags/spark/notebooks/gold_layer/refresh_materialized_views.py)

This file refreshes all materialized views after the ETL process completes.

### When to edit this file:
- Adding new materialized views to be refreshed
- Changing the refresh order

## Best Practices

1. **Always use parameterized queries** when accepting user input to prevent SQL injection
2. **Test queries in psql** before adding them to the code
3. **Use consistent column aliases** across different queries for the same data
4. **Document complex queries** with comments explaining the logic
5. **Keep schema.sql in sync** with actual database structure
6. **Use EXPLAIN ANALYZE** to optimize slow queries

## Common Tasks

### Adding a new statistic to the dashboard:

1. **Update the base table** in `schema.sql` if needed
2. **Create/update materialized view** in `schema.sql` to include the new statistic
3. **Update the query** in `server.py` to return the new column
4. **Update frontend** (`app.js`) to display the new statistic

### Adding a new country-wise aggregation:

1. **Create materialized view** in `schema.sql`:
   ```sql
   CREATE MATERIALIZED VIEW IF NOT EXISTS public.format_role_stats_country_wise AS
    SELECT country, format,
           count(full_name) AS number_of_players,
           sum(your_metric) AS total_your_metric
      FROM public.role_format
     GROUP BY country, format
     WITH NO DATA;
   ```

2. **Add query** to `COUNTRY_QUERIES` in `server.py`:
   ```python
   "role": {
       "Format": "SELECT ... FROM public.format_role_stats_country_wise",
   }
   ```

3. **Update frontend** to display the new data

## Database Connection

The database connection configuration is in `server.py` (lines 34-40):
```python
DB_CONFIG = {
    "host": os.getenv("HOST_NAME", "localhost"),
    "dbname": os.getenv("DATABASE_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "port": os.getenv("PORT", "5432"),
}
```

These values are loaded from the `.env` file in the `dags/` directory.

## Running Queries Manually

To test queries directly against the database:

```bash
# Connect to PostgreSQL
psql -U postgres -d cricket_analyzer

# Run a query
SELECT * FROM public.batsmen_odi LIMIT 10;

# Refresh a materialized view
REFRESH MATERIALIZED VIEW public.player_stats_all_formats_batsmen;
```

## Troubleshooting

### Query returns no data
- Check if the materialized views have been refreshed
- Verify the DAG has run successfully
- Check if base tables have data

### Decimal serialization errors
- The server now handles Decimal types automatically (see `decimal_to_float` function in `server.py`)

### Performance issues
- Add indexes to frequently queried columns
- Use EXPLAIN ANALYZE to identify bottlenecks
- Consider partitioning large tables

## Additional Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Spark SQL Guide: https://spark.apache.org/docs/latest/sql-programming-guide.html
- Project README: See main project documentation for setup instructions