from airflow.decorators import task, dag
from airflow.hooks.base import BaseHook
from datetime import datetime
from include.utils.get_api_details import get_api_details
from datetime import timedelta
from pathlib import Path
from zipfile import ZipFile
import subprocess


@dag(
    dag_id="dag_data",
    start_date=datetime(2026, 6, 1),
    schedule="0 18 22 7 2",
    catchup=False
)
def analytics_dag():

    @task()
    def get_details_from_cricbuzz():
        connection_details = BaseHook.get_connection("kaggle_api_connection")
        host = connection_details.host
        payload = connection_details.extra_dejson

        url = f"{host}{payload['endpoint']}{payload['dataset']}"
        print(f"The url:{url}")

        folder_path = Path("/Users/burugula.sasank/airflow/dags/file_stores/api_dump")
        
        file_path = folder_path / "cric_data.zip"
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"File_path:{file_path}")

        return get_api_details(url,payload,file_path)

    @task()
    def extract_file_content(zip_file_path):

        zip_path = Path(zip_file_path)
        output_path = zip_path.parent / "cric_data"
        output_path.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_path)

        print(f"Extracted to: {output_path}")
        return str(output_path)
    
    @task()
    def ingest_data_to_filesystem(bronze_path):
        subprocess.run(["python3","/Users/burugula.sasank/airflow/dags/spark/notebooks/bronze_layer/ingest_data_to_bronze.py"],check = True)
        print("Bronze Ingestion Success")
        return ""
    
    @task(doc_md = "The picks the data from Bronze Layer and apply transformations on it and pushes it to Gold Layer for advanced aggregations",retries=3, 
        retry_delay=timedelta(seconds=5))
    def transform_data_from_filesystem(silver_path):
        returned_val = subprocess.run(["python3","/Users/burugula.sasank/airflow/dags/spark/notebooks/silver_layer/data_transformations.py"],check = True)
        print(f"Silver Ingestion Success with returned val:{returned_val}")
        return ""
    
    @task(doc_md="Refreshes the dashboard's materialized views (batsmen/bowler/fielder stats, the country-wise views, and the player_stats_all_formats_* views) now that Spark has overwritten the base tables.")
    def refresh_materialized_views(_silver_result):
        dags_dir = Path(__file__).resolve().parent
        script_path = dags_dir / "spark" / "notebooks" / "gold_layer" / "refresh_materialized_views.py"
        subprocess.run(["python3", str(script_path)], check=True)
        return ""

    @task(doc_md="Starts (or reuses) the CricMetrics Pro dashboard server and opens it in the default browser now that Postgres has fresh data.")
    def launch_dashboard(_refresh_result):
        from include.utils.launch_dashboard import launch_dashboard as open_dashboard
        url = open_dashboard()
        print(f"Dashboard opened at {url}")
        return url

    launch_dashboard(
        refresh_materialized_views(
            transform_data_from_filesystem(
                ingest_data_to_filesystem(
                    extract_file_content(get_details_from_cricbuzz())
                )
            )
        )
    )


analytics_dag()