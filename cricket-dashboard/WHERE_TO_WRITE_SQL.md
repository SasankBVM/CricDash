# Where to Write SQL Queries - Simple Guide

This guide maps each UI element in the dashboard to where you write SQL queries for it.

---

## 📍 Location: `cricket-dashboard/server.py`

All SQL queries for the dashboard are written in **ONE FILE**: [`cricket-dashboard/server.py`](server.py)

---

## 🎯 UI Element → SQL Query Location

### 1️⃣ **OVERVIEW TAB** - Player Statistics

**What you see:** Individual player stats (runs, average, strike rate, etc.)

**Where to write SQL:** Lines 56-134 in `server.py`

**Query Dictionary:** `PLAYER_QUERIES`

```python
PLAYER_QUERIES = {
    "batsmen": {
        "ODI": "SELECT full_name, country, ... FROM public.batsmen_odi",
        "T20": "SELECT full_name, country, ... FROM public.batsmen_t20", 
        "Test": "SELECT full_name, country, ... FROM public.batsmen_test",
        "All": "SELECT full_name, country, ... FROM public.batsmen_stats"
    },
    "bowler": {
        "ODI": "SELECT full_name, country, ... FROM public.bowler_odi",
        "T20": "SELECT full_name, country, ... FROM public.bowler_t20",
        "Test": "SELECT full_name, country, ... FROM public.bowler_test", 
        "All": "SELECT full_name, country, ... FROM public.bowler_stats"
    },
    "fielder": {
        "ODI": "SELECT full_name, country, ... FROM public.fielder_odi",
        "T20": "SELECT full_name, country, ... FROM public.fielder_t20",
        "Test": "SELECT full_name, country, ... FROM public.fielder_test",
        "All": "SELECT full_name, country, ... FROM public.fielder_stats"
    }
}
```

**Example - Add a new column to batting stats:**
```python
"ODI": """
    SELECT full_name, country, years_active, matches_played,
           "Runs" AS runs, average, strike_rate,
           your_new_column,  -- ← ADD YOUR NEW COLUMN HERE
           format
      FROM public.batsmen_odi
"""
```

---

### 2️⃣ **ADVANCED ANALYTICS TAB** → **Player Rankings** Sub-tab

**What you see:** Table showing all-format player rankings

**Where to write SQL:** Lines 136-140 in `server.py`

**Query Dictionary:** `RANKINGS_QUERIES`

```python
RANKINGS_QUERIES = {
    "batsmen": "SELECT * FROM public.player_stats_all_formats_batsmen",
    "bowler": "SELECT * FROM public.player_stats_all_formats_bowler",
    "fielder": "SELECT * FROM public.player_stats_all_formats_fielder"
}
```

**Example - Change what columns are shown:**
```python
"batsmen": """
    SELECT full_name, country, total_runs, total_matches, total_average
      FROM public.player_stats_all_formats_batsmen
     ORDER BY total_runs DESC
"""
```

---

### 3️⃣ **ADVANCED ANALYTICS TAB** → **Country Stats** Sub-tab

**What you see:** Blocks showing statistics for each country

**Where to write SQL:** Lines 145-249 in `server.py`

**Query Dictionary:** `COUNTRY_QUERIES`

```python
COUNTRY_QUERIES = {
    "batsmen": {
        "ODI": "SELECT country, format, number_of_players, total_runs, ... FROM public.odi_batsmen_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_runs, ... FROM public.t20_batsmen_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_runs, ... FROM public.test_batsmen_stats_country_wise",
        "All": "SELECT country, 'All' AS format, SUM(...) ... (combines all formats)"
    },
    "bowler": {
        "ODI": "SELECT country, format, number_of_players, total_wickets, ... FROM public.odi_bowler_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_wickets, ... FROM public.t20_bowler_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_wickets, ... FROM public.test_bowler_stats_country_wise",
        "All": "SELECT country, 'All' AS format, SUM(...) ... (combines all formats)"
    },
    "fielder": {
        "ODI": "SELECT country, format, number_of_players, total_dismissals, ... FROM public.odi_fielder_stats_country_wise",
        "T20": "SELECT country, format, number_of_players, total_dismissals, ... FROM public.t20_fielder_stats_country_wise",
        "Test": "SELECT country, format, number_of_players, total_dismissals, ... FROM public.test_fielder_stats_country_wise",
        "All": "SELECT country, 'All' AS format, SUM(...) ... (combines all formats)"
    }
}
```

**Example - Add a new stat to country blocks:**
```python
"ODI": """
    SELECT country, format, number_of_players, total_runs,
           average_batting_average, average_strike_rate,
           your_new_stat,  -- ← ADD YOUR NEW STAT HERE
           total_hundreds, total_fifties, total_ducks
      FROM public.odi_batsmen_stats_country_wise
"""
```

---

## 🔧 Quick Reference

| UI Element | File | Line Numbers | Dictionary Name |
|------------|------|--------------|-----------------|
| Player Stats (Overview) | `server.py` | 56-134 | `PLAYER_QUERIES` |
| Player Rankings (Analytics) | `server.py` | 136-140 | `RANKINGS_QUERIES` |
| Country Stats (Analytics) | `server.py` | 145-249 | `COUNTRY_QUERIES` |

---

## 📝 How to Add/Modify Queries

### Step 1: Open `server.py`
```bash
code cricket-dashboard/server.py
```

### Step 2: Find the right dictionary
- Player stats? → `PLAYER_QUERIES` (line 56)
- Rankings? → `RANKINGS_QUERIES` (line 136)
- Country stats? → `COUNTRY_QUERIES` (line 145)

### Step 3: Edit the SQL query
- Add/remove columns in the SELECT statement
- Change the FROM table if needed
- Add WHERE clauses for filtering
- Modify ORDER BY for sorting

### Step 4: Save and restart the server
```bash
python3 cricket-dashboard/server.py
```

---

## ⚠️ Important Notes

1. **Column names must match** what the frontend expects (check `app.js` if unsure)
2. **Always use aliases** for clarity: `"Runs" AS runs`
3. **Test your query** in psql first before adding to server.py
4. **The "All" format** usually combines data from ODI, T20, and Test using UNION ALL

---

## 💡 Common Tasks

### Add a new statistic to player overview:
1. Go to line 56 in `server.py`
2. Find the role (batsmen/bowler/fielder)
3. Add your column to the SELECT statement
4. Do this for all formats (ODI, T20, Test, All)

### Change what's shown in country blocks:
1. Go to line 145 in `server.py`
2. Find the role (batsmen/bowler/fielder)
3. Modify the SELECT columns
4. Update for all formats

### Modify player rankings:
1. Go to line 136 in `server.py`
2. Change the SELECT or add WHERE/ORDER BY clauses

---

## 🎓 Example: Adding "Sixes" to Batting Stats

```python
# In PLAYER_QUERIES dictionary, update each format:

"ODI": """
    SELECT full_name, country, years_active, matches_played,
           "Runs" AS runs, average, strike_rate,
           hundreds, fifties, ducks,
           number_of_sixes AS sixes,  -- ← NEW COLUMN
           format
      FROM public.batsmen_odi
""",

# Repeat for T20, Test, and All formats
```

That's it! The query is now updated and will show sixes in the UI.