import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

RAW_DIR = os.getenv(
    "XKCD_HDFS_RAW_DIR",
    "hdfs://namenode:8020/user/hadoop/xkcd/raw",
)

FINAL_DIR = os.getenv(
    "XKCD_HDFS_FINAL_DIR",
    "hdfs://namenode:8020/user/hadoop/xkcd/final",
)

def main():
    spark = (
        SparkSession.builder
            .appName("XKCD-Raw-To-Final")
            .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:        
        # ========================================
        # 1. Extract
        # ========================================
        print("Reading raw XKCD data from HDFS...")

        raw = (
            spark.read
                .option("multiLine", "true")
                .option("recursiveFileLookup", "true")
                .option("pathGlobFilter", "*.json")
                .json(RAW_DIR)
        )

        raw_count = raw.count()
        print(f"Raw records: {raw_count}")

        if raw_count == 0:
            raise ValueError("No XKCD records found.")

        
        # ========================================
        # 2. Transform
        # ========================================
        # Keep relevant fields
        cleaned = raw.select(
            F.col("num").cast("int").alias("id"),
            F.col("year").cast("int").alias("year"),
            F.col("month").cast("int").alias("month"),
            F.col("day").cast("int").alias("day"),
            F.trim(F.col("title")).alias("title"),
            F.trim(F.col("safe_title")).alias("safe_title"),
            F.trim(F.col("alt")).alias("alt"),
            F.trim(F.col("transcript")).alias("transcript"),
            F.trim(F.col("img")).alias("image_url"),
        )

        # Remove invalid records
        cleaned = cleaned.filter(
            (F.col("id").isNotNull())
            & (F.col("id") > 0)
            & F.col("year").isNotNull()
            & F.col("title").isNotNull()
            & (F.length("title") > 0)
            & F.col("image_url").isNotNull()
            & (F.length("image_url") > 0)
        )

        # Remove duplicate comics
        cleaned = cleaned.dropDuplicates(["id"])

        # Generate canonical XKCD URL
        cleaned = cleaned.withColumn(
            "comic_url",
            F.concat(
                F.lit("https://xkcd.com/"),
                F.col("id").cast("string"),
                F.lit("/"),
            ),
        )

        # Build searchable text
        cleaned = cleaned.withColumn(
            "search_text",
            F.lower(
                F.concat_ws(
                    " ",
                    F.coalesce(F.col("title"), F.lit("")),
                    F.coalesce(F.col("alt"), F.lit("")),
                    F.coalesce(F.col("transcript"), F.lit("")),
                )
            ),
        )

        final_count = cleaned.count()

        print(f"Final records: {final_count}")
        print(f"Removed records: {raw_count - final_count}")


        # ========================================
        # 3. Load
        # ========================================
        print("Writing Parquet data to HDFS...")

        (
            cleaned
            .repartition(4)
            .write
            .mode("overwrite")
            .parquet(FINAL_DIR)
        )

        print("Transformation finished successfully!")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()