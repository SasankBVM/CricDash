# 🏏 CricDash - Cricket Analytics Data Pipeline

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.0+-red.svg)](https://airflow.apache.org/)
[![Spark](https://img.shields.io/badge/Apache%20Spark-3.0+-orange.svg)](https://spark.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)

> End-to-end data engineering pipeline for cricket analytics using Apache Airflow, Spark, and PostgreSQL with medallion architecture (Bronze → Silver → Gold).

---

## 🎯 Project Overview

**CricDash** is a production-grade data engineering project that demonstrates:
- **Automated ETL Pipeline** using Apache Airflow
- **Distributed Processing** with Apache Spark (PySpark)
- **Medallion Architecture** (Bronze-Silver-Gold layers)
- **Optimized Data Warehouse** with PostgreSQL materialized views
- **RESTful API** for data serving

### Key Achievements
- ⚡ **50x faster queries** using materialized views (5s → 100ms)
- 📊 **Processes 100K+ records** across 9 tables and 15 views
- 🔄 **Automated workflow** with retry logic and monitoring
- 💾 **70% storage reduction** using Parquet compression

---

## 🏗️ Architecture

```
Kaggle API → Airflow DAG → Spark Processing → PostgreSQL → Web Dashboard
                    ↓              ↓                ↓
                Bronze Layer   Silver Layer    Gold Layer
                (Raw Data)     (Cleaned)       (Aggregated)
```

### Data Flow
1. **Extract**: Fetch cricket data from Kaggle API
2. **Bronze**: Store raw data in Parquet format
3. **Silver**: Clean, validate, and transform using Spark
4. **Gold**: Create materialized views for fast queries
5. **Serve**: RESTful API serves data to dashboard

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Apache Airflow | Workflow management & scheduling |
| **Processing** | Apache Spark (PySpark) | Distributed data transformation |
| **Storage** | PostgreSQL + Parquet | Data warehouse & data lake |
| **API** | Python HTTP Server | RESTful endpoints |
| **Frontend** | HTML/CSS/JavaScript | Interactive dashboard |

---

## 📁 Project Structure

```
CricDash/
├── dags/
│   ├── dag_data.py                    # Airflow DAG (orchestration)
│   ├── spark/notebooks/
│   │   ├── bronze_layer/              # Raw data ingestion
│   │   ├── silver_layer/              # Data transformation (Spark)
│   │   └── gold_layer/                # Materialized views
│   └── file_stores/                   # Data lake (Parquet files)
│
├── cricket-dashboard/
│   ├── server.py                      # Python API server
│   ├── sql/schema.sql                 # Database schema
│   └── [index.html, app.js, styles.css]
│
└── README.md
```

---

## 🔄 Data Pipeline

### Airflow DAG Workflow

```python
extract_api → parse_json → bronze_layer → silver_layer → gold_layer
```

### Medallion Architecture

#### 🥉 Bronze Layer
- **Input**: JSON from Kaggle API
- **Process**: Minimal transformation, schema validation
- **Output**: Parquet files (partitioned by format)
- **Storage**: `file_stores/bronze_layer/`

#### 🥈 Silver Layer (Spark Transformations)
- **Input**: Bronze Parquet files
- **Process**: 
  - Data cleaning & standardization
  - Null handling & deduplication
  - Type casting & validation
- **Output**: 9 PostgreSQL tables (3 roles × 3 formats)

#### 🥇 Gold Layer
- **Input**: Silver tables
- **Process**: Aggregations & materialized views
- **Output**: 15 optimized views for analytics
- **Performance**: Sub-second query response

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+ | PostgreSQL 13+ | Apache Spark 3.0+ | Apache Airflow 2.0+
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/SasankBVM/CricDash.git
cd CricDash

# 2. Install dependencies
pip install apache-airflow pyspark psycopg2-binary python-dotenv

# 3. Setup PostgreSQL
createdb cricket_analyzer
psql -d cricket_analyzer -f cricket-dashboard/sql/schema.sql

# 4. Configure environment
cp dags/.env.example dags/.env
# Edit dags/.env with your database credentials

# 5. Initialize Airflow
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --username admin --password admin --role Admin

# 6. Start Airflow
airflow webserver -p 8080  # Terminal 1
airflow scheduler           # Terminal 2

# 7. Trigger pipeline
airflow dags trigger dag_data

# 8. Start dashboard
cd cricket-dashboard && python server.py
```

Access:
- **Airflow UI**: http://localhost:8080
- **Dashboard**: http://localhost:8000

---

## 📊 Database Schema

### Base Tables (9)
- `batsmen_{format}` - Batting statistics
- `bowler_{format}` - Bowling statistics  
- `fielder_{format}` - Fielding statistics

### Materialized Views (15)
- **Level 1**: Combined format views (3)
- **Level 2**: All-format player stats (3)
- **Level 3**: Country-wise statistics (9)

### Performance Optimization
```sql
-- Materialized views for fast queries
CREATE MATERIALIZED VIEW player_stats_all_formats_batsmen AS
SELECT full_name, SUM(runs) as total_runs, ...
FROM batsmen_stats GROUP BY full_name;

-- Indexes for common queries
CREATE INDEX idx_runs ON batsmen_odi(runs DESC);
```

---

> **📌 Data Note:** This project is built on existing historical cricket data sourced from Kaggle datasets. Statistics for senior, well-established players are generally accurate and complete. However, numbers for junior or lesser-known players may be incomplete or contain inaccuracies due to gaps in the source data. This project is intended for learning and portfolio demonstration purposes, not as an authoritative statistical reference.

---

## ⚡ Key Features

### Data Engineering
✅ **Automated ETL** - Airflow DAG with 5 tasks  
✅ **Distributed Processing** - Spark handles large datasets  
✅ **Data Quality** - Validation, deduplication, error handling  
✅ **Incremental Loading** - Bronze → Silver → Gold layers  
✅ **Fault Tolerance** - Retry logic & monitoring  

### Performance
✅ **Query Speed**: 100ms (vs 5s without optimization)  
✅ **Storage**: 70% reduction with Parquet  
✅ **Scalability**: Handles 100K+ records  
✅ **Caching**: Spark in-memory computation  

### Dashboard
✅ **Player Rankings** - Top performers by format  
✅ **Country Stats** - Aggregated metrics by nation  
✅ **Comparisons** - Side-by-side player analysis  
✅ **RESTful API** - Clean, documented endpoints  

---

## 🔌 API Endpoints

```bash
# Health check
GET /api/health

# Player data
GET /api/players?role=batsmen&format=ODI

# Rankings (all formats)
GET /api/rankings?role=batsmen

# Country statistics
GET /api/country-stats?role=batsmen&format=Test&country=India

# Countries list
GET /api/countries
```

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Pipeline Duration | 7 minutes |
| Query Response Time | < 100ms |
| Records Processed | 100,000+ |
| Storage Efficiency | 70% reduction |
| Tables + Views | 24 objects |

---

## 🎓 Skills Demonstrated

### Data Engineering
- ETL pipeline design & implementation
- Workflow orchestration (Airflow)
- Distributed computing (Spark)
- Data modeling & warehousing
- Performance optimization

### Technologies
- Python (PySpark, pandas, requests)
- SQL (PostgreSQL, materialized views)
- Apache Airflow (DAGs, operators)
- Apache Spark (transformations, actions)
- RESTful API development

### Best Practices
- Medallion architecture
- Data quality validation
- Error handling & logging
- Environment-based configuration
- Version control (Git)

---

## 📝 Future Enhancements

- [ ] Real-time data streaming (Kafka)
- [ ] Machine learning predictions
- [ ] Advanced analytics (time-series)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Containerization (Docker)
- [ ] Cloud deployment (AWS/GCP)

---

## 👨‍💻 Author

**Sasank BVM**

[![GitHub](https://img.shields.io/badge/GitHub-SasankBVM-black?logo=github)](https://github.com/SasankBVM)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://www.linkedin.com/in/bvm-sasank-1524b6200/)

---

## 📄 License

MIT License - feel free to use this project for learning and portfolio purposes.

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

*Built with Apache Airflow, Spark, and PostgreSQL*

</div>
