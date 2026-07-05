from pyspark.sql import SparkSession,DataFrame
from pyspark.sql.functions import col,udf,lit
from pyspark.sql.types import StringType,StructType,StructField,IntegerType,FloatType
from collections import Counter
import os,sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

# Forces workers to use the same Python executable as the current driver/kernel
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


return_schema = StructType([
    StructField("full_name",StringType(),True),
    StructField("country",StringType(),True)
]
)

@udf(returnType=return_schema)
def get_full_name_and_country(string:str) -> str:
    countries = {"INDIA":"India","BMUDA":"Bermuda","SL":"Sri Lanka","NZ":"New Zealand","WI":"West Indies","BDESH":"Bangladesh",
                 "ZIM":"Zimbabwe","AUS":"Australia","AFG":"Afganisthan","SA":"South Africa",
                 "ENG":"England","IRE":"Ireland","PNG":"Papua New Guinea","EAf":"Kenya",
                 "PAK":"Pakistan", "NAM":"Namibia","UAE":"United Arab Emirates",
                 "HKG":"HongKonng","NL":"Netherlands","SCOT":"Scotland","CAN":"Canada","Afr/KENYA":"Kenya",
                 "KENYA":"Kenya","NEPAL":"Nepal"
                 }
    name_tokens = string.split(" ")
    full_name = ""
    country = ""
    found = False
    for name in name_tokens:
        if name.__contains__("("):
            country = name[1:-1]
        else:
            full_name+=f"{name} "
    
    for key in countries.keys():
        if key in country:
            country = countries[key]
            found = True
            break
    
    return (full_name[:-1],country) if found else (None,None)

def parse_names_country(input_df:DataFrame) -> DataFrame:
    processed_input_df =input_df.withColumn("full_name_object",get_full_name_and_country(col("Player")))\
    .withColumn("full_name",col("full_name_object.full_name"))\
    .withColumn("country",col("full_name_object.country"))\
    .drop("full_name_object","Player")\
    .filter(col("full_name").isNotNull())\
    
    for column in processed_input_df.columns:
        if "Unnamed" in column:
            processed_input_df = processed_input_df.drop(column)
            break

    columns = processed_input_df.columns
    column_order = [columns[-2],columns[-1]]+columns[1:-2]
    return processed_input_df.select(column_order)

@udf(returnType=StringType())
def resolve_highest_score(score_str:str) -> str:
    if "*" in score_str:
        return score_str[:-1]
    return score_str

@udf(returnType=IntegerType())
def calculate_span_years(span:str) -> int:
    range_years = span.split("-")
    from_year = int(range_years[0])
    to_year= int(range_years[1])
    return to_year-from_year

@udf(returnType=IntegerType())
def extract_balls_from_overs(over_string:str) -> int:
    if over_string.__contains__("."):
        number_of_balls = over_string.split(".")
        return int(number_of_balls[0])*6 + int(number_of_balls[1])
    else:
        return 0


def rename_column(input_df: DataFrame,df_type:str) -> DataFrame:
    columns = Counter(input_df.columns)

    input_df = input_df.withColumnRenamed("Mat","matches_played").\
        withColumnRenamed("Inns","innings_played").\
        withColumnRenamed("Ave","average").\
        withColumnRenamed("SR","strike_rate")

    if columns.get("4s",None):
        input_df = input_df.withColumnRenamed("4s","number_of_fours")
    
    if columns.get("6s",None):
        input_df = input_df.withColumnRenamed("6s","number_of_sixes")
    

    if df_type == "batsmen":
        return input_df.withColumnRenamed("BF","balls_faced").\
        withColumnRenamed("100","hundreds").\
        withColumnRenamed("50","fifties").\
        withColumnRenamed("0","ducks").\
        withColumnRenamed("NO","not_outs")
    
    elif df_type == "bowler":
        input_df = input_df.withColumnRenamed("Wkts","wickets").\
        withColumnRenamed("Econ","economy").\
        withColumnRenamed("4","four_wicket_hauls").\
        withColumnRenamed("5","five_wicket_hauls")
        if columns.get("Mdns",None):
            input_df = input_df.withColumnRenamed("Mdns","number_of_maidens")
        return input_df
    else:
        return input_df.withColumnRenamed("Dis","dismissals").\
        withColumnRenamed("Ct","catches").\
        withColumnRenamed("St","stumpings").\
        withColumnRenamed("Ct Wk","catch_wickets").\
        drop("Ct Fi","MD","D/I")

def change_data_types(input_df: DataFrame, df_type: str) -> DataFrame:
    columns = Counter(input_df.columns)
    input_df = input_df.withColumn("matches_played",col("matches_played").try_cast(IntegerType())).\
        withColumn("innings_played",col("innings_played").try_cast(IntegerType()))
    
    if df_type == "batsmen":
        input_df = input_df.withColumn("Runs",col("Runs").try_cast(IntegerType())).\
        withColumn("highest_score",col("highest_score").try_cast(IntegerType())).\
        withColumn("hundreds",col("hundreds").try_cast(IntegerType())).\
        withColumn("fifties",col("fifties").try_cast(IntegerType())).\
        withColumn("ducks",col("ducks").try_cast(IntegerType())).\
        withColumn("not_outs",col("not_outs").try_cast(IntegerType()))

        if columns.get("balls_faced",None):
            input_df = input_df.withColumn("balls_faced",col("balls_faced").try_cast(IntegerType()))
        if columns.get("strike_rate",None):
            input_df = input_df.withColumn("strike_rate",col("strike_rate").try_cast(FloatType()))
        if columns.get("average",None):
            input_df = input_df.withColumn("average",col("average").try_cast(FloatType()))
        
        if columns.get("number_of_fours",None):
            input_df = input_df.withColumn("number_of_fours",col("number_of_fours").try_cast(IntegerType()))
        
        if columns.get("number_of_sixes",None):
            input_df = input_df.withColumn("number_of_sixes",col("number_of_sixes").try_cast(IntegerType()))

        return input_df
        
    
    elif df_type == "bowler":
        input_df = input_df.withColumn("wickets",col("wickets").try_cast(IntegerType())).\
        withColumn("economy",col("economy").try_cast(FloatType())).\
        withColumn("five_wicket_hauls",col("five_wicket_hauls").try_cast(IntegerType())).\
        withColumn("average",col("average").try_cast(FloatType())).\
        withColumn("Runs",col("Runs").try_cast(IntegerType())).\
        withColumn("strike_rate",col("strike_rate").try_cast(FloatType()))
        

        if columns.get("four_wicket_hauls",None):
            input_df = input_df.withColumn("four_wicket_hauls",col("four_wicket_hauls").try_cast(IntegerType()))
        
        if columns.get("number_of_maidens",None):
            input_df = input_df.withColumn("number_of_maidens",col("number_of_maidens").try_cast(IntegerType()))
        
        if columns.get("Balls",None):
            input_df = input_df.withColumn("Balls",col("Balls").try_cast(IntegerType()))
        
        if columns.get("Overs",None):
            input_df = input_df.withColumn("Overs",extract_balls_from_overs(col("Overs")))
        
        return input_df
    
    else:
        return input_df.withColumn("dismissals",col("dismissals").try_cast(IntegerType())).\
        withColumn("catches",col("catches").try_cast(IntegerType())).\
        withColumn("stumpings",col("stumpings").try_cast(IntegerType())).\
        withColumn("catch_wickets",col("catch_wickets").try_cast(IntegerType()))


def erase_stale_data():
    stale_materialized_views = ["batsmen_stats","bowler_stats","fielder_stats","odi_batsmen_stats_country_wise",
                                "odi_bowler_stats_country_wise","odi_fielder_stats_country_wise",
                                "player_stats_all_formats_batsmen","player_stats_all_formats_bowler",
                                "player_stats_all_formats_fielder","t20_batsmen_stats_country_wise",
                                "t20_bowler_stats_country_wise","t20_fielder_stats_country_wise",
                                "test_batsmen_stats_country_wise","test_bowler_stats_country_wise",
                                "test_fielder_stats_country_wise"
                                ]
    database_schema = os.getenv("DATABASE_SCHEMA", "public")
    db_args = {
        "dbname":os.getenv("DATABASE_NAME"),
        "user":os.getenv("USER_NAME"),
        "password":os.getenv("PASSWORD"),
        "host":os.getenv("HOST_NAME"),
        "port":os.getenv("PORT")
    }
    try:
        print(".....Connection with the database is successfull......")
        conn = psycopg2.connect(**db_args)
        cursor = conn.cursor()

        for view_name in stale_materialized_views:
            cursor.execute(
                sql.SQL("DROP MATERIALIZED VIEW IF EXISTS {}.{} CASCADE").format(
                    sql.Identifier(database_schema),
                    sql.Identifier(view_name)
                )
            )

        conn.commit()
        cursor.close()
        conn.close()

        print(".....Erased stale materialized views......")
    except Exception as e:
        print(f"The exception is {e}")

def write_to_database(input_df,dbtable):

    input_df.write.format("jdbc").mode("overwrite").option("url",os.getenv("DATABASE_URL")).\
option("driver",os.getenv("DATABASE_DRIVER")).option("dbtable",dbtable).option("user",os.getenv("USER_NAME")).option("cascadeTruncate", "true").option("password",os.getenv("PASSWORD")).save()


spark = SparkSession.builder.\
        appName("data_transformations").\
        master("local[*]").\
        config("spark.jars.packages", "org.postgresql:postgresql:42.7.3"). \
        getOrCreate()


# 1. Reading Data From Bronze

# Batting Data
data_bronze_batsmen_odi  = spark.read.load("dags/file_stores/bronze_layer/Batting/ODI")
data_bronze_batsmen_t20  = spark.read.load("dags/file_stores/bronze_layer/Batting/T20/")
data_bronze_batsmen_test = spark.read.load("dags/file_stores/bronze_layer/Batting/Test/")


# Bowling Data
data_bronze_bowler_odi   = spark.read.load("dags/file_stores/bronze_layer/Bowling/ODI/")
data_bronze_bowler_t20   = spark.read.load("dags/file_stores/bronze_layer/Bowling/T20/")
data_bronze_bowler_test  = spark.read.load("dags/file_stores/bronze_layer/Bowling/Test/")


# Fielding Data
data_bronze_fielder_odi  = spark.read.load("dags/file_stores/bronze_layer/Fielding/ODI/")
data_bronze_fielder_t20  = spark.read.load("dags/file_stores/bronze_layer/Fielding/T20/")
data_bronze_fielder_test = spark.read.load("dags/file_stores/bronze_layer/Fielding/Test/")

# 2. Extracting Full Name and Country & dropping unnecessary columns

# Batting Transformations
data_silver_batsmen_odi  = parse_names_country(data_bronze_batsmen_odi)
data_silver_batsmen_t20  = parse_names_country(data_bronze_batsmen_t20)
data_silver_batsmen_test = parse_names_country(data_bronze_batsmen_test)

# Bowling Transformations
data_silver_bowler_odi   = parse_names_country(data_bronze_bowler_odi)
data_silver_bowler_t20   = parse_names_country(data_bronze_bowler_t20)
data_silver_bowler_test  = parse_names_country(data_bronze_bowler_test)

# Fielding Transformations
data_silver_fielder_odi  = parse_names_country(data_bronze_fielder_odi)
data_silver_fielder_t20  = parse_names_country(data_bronze_fielder_t20)
data_silver_fielder_test = parse_names_country(data_bronze_fielder_test)

# 3. Resolving * issue in Highest score
data_silver_batsmen_odi = data_silver_batsmen_odi.withColumn("HS",resolve_highest_score(col("HS"))).withColumnRenamed("HS","highest_score")
data_silver_batsmen_t20 = data_silver_batsmen_t20.withColumn("HS",resolve_highest_score(col("HS"))).withColumnRenamed("HS","highest_score")
data_silver_batsmen_test = data_silver_batsmen_test.withColumn("HS",resolve_highest_score(col("HS"))).withColumnRenamed("HS","highest_score")

# 4. Calculating Years Active
data_silver_batsmen_odi = data_silver_batsmen_odi.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("ODI"))
data_silver_batsmen_t20 = data_silver_batsmen_t20.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("T20"))
data_silver_batsmen_test = data_silver_batsmen_test.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("Test"))

data_silver_bowler_odi = data_silver_bowler_odi.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("ODI"))
data_silver_bowler_t20 = data_silver_bowler_t20.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("T20"))
data_silver_bowler_test = data_silver_bowler_test.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("Test"))

data_silver_fielder_odi = data_silver_fielder_odi.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("ODI"))
data_silver_fielder_t20 = data_silver_fielder_t20.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("T20"))
data_silver_fielder_test = data_silver_fielder_test.withColumn("Span",calculate_span_years(col("Span"))).withColumnRenamed("Span","years_active").withColumn("format",lit("Test"))


# 5. Renaming the columns
data_silver_batsmen_odi = rename_column(data_silver_batsmen_odi,"batsmen")
data_silver_batsmen_t20 = rename_column(data_silver_batsmen_t20,"batsmen")
data_silver_batsmen_test = rename_column(data_silver_batsmen_test,"batsmen")

data_silver_bowler_odi = rename_column(data_silver_bowler_odi,"bowler")
data_silver_bowler_t20 = rename_column(data_silver_bowler_t20,"bowler")
data_silver_bowler_test = rename_column(data_silver_bowler_test,"bowler")

data_silver_fielder_odi = rename_column(data_silver_fielder_odi,"fielder")
data_silver_fielder_t20 = rename_column(data_silver_fielder_t20,"fielder")
data_silver_fielder_test = rename_column(data_silver_fielder_test,"fielder")

# 6. Casting the dtypes of the columns

data_silver_batsmen_odi = change_data_types(data_silver_batsmen_odi,"batsmen")
data_silver_batsmen_t20 = change_data_types(data_silver_batsmen_t20,"batsmen")
data_silver_batsmen_test = change_data_types(data_silver_batsmen_test,"batsmen")

data_silver_bowler_odi = change_data_types(data_silver_bowler_odi,"bowler")
data_silver_bowler_t20 = change_data_types(data_silver_bowler_t20,"bowler")
data_silver_bowler_test = change_data_types(data_silver_bowler_test,"bowler")

data_silver_fielder_odi = change_data_types(data_silver_fielder_odi,"fielder")
data_silver_fielder_t20 = change_data_types(data_silver_fielder_t20,"fielder")
data_silver_fielder_test = change_data_types(data_silver_fielder_test,"fielder")

# 7. Remove Duplicates - Keep only unique player records
data_silver_batsmen_odi = data_silver_batsmen_odi.distinct()
data_silver_batsmen_t20 = data_silver_batsmen_t20.distinct()
data_silver_batsmen_test = data_silver_batsmen_test.distinct()

data_silver_bowler_odi = data_silver_bowler_odi.distinct()
data_silver_bowler_t20 = data_silver_bowler_t20.distinct()
data_silver_bowler_test = data_silver_bowler_test.distinct()

data_silver_fielder_odi = data_silver_fielder_odi.distinct()
data_silver_fielder_t20 = data_silver_fielder_t20.distinct()
data_silver_fielder_test = data_silver_fielder_test.distinct()

# 8. Erasing Stale data/views
erase_stale_data()

# 9. Pushing To Silver Files For Further Advanced Aggregations (GOLD Layer)

write_to_database(data_silver_batsmen_odi,"batsmen_odi")
write_to_database(data_silver_batsmen_t20,"batsmen_t20")
write_to_database(data_silver_batsmen_test,"batsmen_test")

write_to_database(data_silver_bowler_odi,"bowler_odi")
write_to_database(data_silver_bowler_t20,"bowler_t20")
write_to_database(data_silver_bowler_test,"bowler_test")

write_to_database(data_silver_fielder_odi,"fielder_odi")
write_to_database(data_silver_fielder_t20,"fielder_t20")
write_to_database(data_silver_fielder_test,"fielder_test")

print(data_silver_fielder_odi.columns)
print(data_silver_fielder_t20.columns)
print(data_silver_fielder_test.columns)
