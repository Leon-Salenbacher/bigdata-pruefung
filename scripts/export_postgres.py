import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

FINAL_DIR = os.getenv(
    "XKCD_HDFS_FINAL_DIR",
    "hdfs://namenode:8020/user/hadoop/xkcd/final"
)

JDBC_URL = os.environ["POSTGRES_JDBC_URL"]
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]

def main():
    spark = (
        SparkSession.builder
            .appName("XKCD-Parquet-To-PostgreSQL")
            .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        # ========================================
        # 1. Read Parquet data from HDFS
        # ========================================
        print("Reading Parquet data from HDFS...")
        comics = spark.read.parquet(FINAL_DIR)

        # Explicitly select expected columns
        comics = comics.select(
            "id",
            "year",
            "month",
            "day",
            "title",
            "safe_title",
            "alt",
            "transcript",
            "image_url",
            "comic_url",
            "search_text",
        )

        # Basic validation
        comics = comics.filter(
            F.col("id").isNotNull()
            & F.col("title").isNotNull()
            & F.col("image_url").isNotNull()
        )

        comics = comics.dropDuplicates(["id"])
        count = comics.count()

        if count == 0:
            raise ValueError("No valid comics found in Parquet data.")

        print(f"Comics to export: {count}")


        # ========================================
        # 2. Write staging table to PostgreSQL
        # ========================================
        print("Writing PostgreSQL staging table...")

        (

            comics.repartition(2)
            .write
            .format("jdbc")
            .option("url", JDBC_URL)
            .option("dbtable", "public.comics_staging")
            .option("user", DB_USER)
            .option("password", DB_PASSWORD)
            .option("driver", "org.postgresql.Driver")
            .option("batchsize", "500")
            .mode("overwrite")
            .save()
        )
        print("Staging export completed successfully!")

    finally:
        spark.stop()

if __name__ == "__main__":
    main()