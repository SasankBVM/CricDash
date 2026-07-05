import os, subprocess,dotenv
import sys, json
from pathlib import Path
from dotenv import load_dotenv

os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
os.environ["PYSPARK_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

load_dotenv()

spark = SparkSession.builder \
    .appName("VSCodeTest") \
    .master("local[*]") \
    .getOrCreate()


def parse_file_contents():

    df_batsmen_odi = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Batting/ODI data.csv", inferSchema=True, header=True)
    df_batsmen_odi.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Batting/ODI/")

    df_batsmen_t20 = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Batting/t20.csv", inferSchema=True, header=True)
    df_batsmen_t20.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Batting/T20/")

    df_batsmen_test = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Batting/test.csv", inferSchema=True, header=True)
    df_batsmen_test.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Batting/Test/")

    df_bowling_odi = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Bowling/Bowling_ODI.csv", inferSchema=True, header=True)
    df_bowling_odi.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Bowling/ODI/")

    df_bowling_t20 = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Bowling/Bowling_t20.csv", inferSchema=True, header=True)
    df_bowling_t20.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Bowling/T20/")

    df_bowling_test = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Bowling/Bowling_test.csv", inferSchema=True, header=True)
    df_bowling_test.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Bowling/Test/")

    df_fielding_odi = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Fielding/Fielding_ODI.csv", inferSchema=True, header=True)
    df_fielding_odi.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Fielding/ODI/")

    df_fielding_t20 = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Fielding/Fielding_t20.csv", inferSchema=True, header=True)
    df_fielding_t20.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Fielding/T20/")

    df_fielding_test = spark.read.csv("/Users/burugula.sasank/airflow/dags/file_stores/api_dump/cric_data/Fielding/Fielding_test.csv", inferSchema=True, header=True)
    df_fielding_test.write.mode("overwrite").option("overwriteSchema", "true").save("/Users/burugula.sasank/airflow/dags/file_stores/bronze_layer/Fielding/Test/")
    
    print("Sample Data (ODI Batsmen):")
    df_batsmen_odi.show(2)

parse_file_contents()
spark.stop()