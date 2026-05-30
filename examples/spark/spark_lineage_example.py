#!/usr/bin/env python3
"""
Spark lineage example using the generic LineageTracker.

This script demonstrates a simple Spark pipeline and emits OpenLineage
START/COMPLETE events to Marquez.
"""

import os
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
PYTHON_EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples", "python")

# Reuse the shared generic tracker from examples/python.
if PYTHON_EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, PYTHON_EXAMPLES_DIR)

from lineage_tracker import LineageTracker


DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MARQUEZ_URL = os.getenv("MARQUEZ_URL", "http://localhost:5050")


def spark_type_to_openlineage(dtype: Any) -> str:
    """Map Spark SQL data types to OpenLineage-friendly SQL type names."""
    from pyspark.sql import types as t

    if isinstance(dtype, t.IntegerType):
        return "INTEGER"
    if isinstance(dtype, t.LongType):
        return "BIGINT"
    if isinstance(dtype, t.FloatType):
        return "FLOAT"
    if isinstance(dtype, t.DoubleType):
        return "DOUBLE"
    if isinstance(dtype, t.BooleanType):
        return "BOOLEAN"
    if isinstance(dtype, t.TimestampType):
        return "TIMESTAMP"
    if isinstance(dtype, t.DateType):
        return "DATE"
    return "VARCHAR"


def schema_from_spark_df(df: Any) -> list[dict[str, str]]:
    """Build OpenLineage schema fields from a Spark DataFrame schema."""
    return [{"name": field.name, "type": spark_type_to_openlineage(field.dataType)} for field in df.schema.fields]


def write_input_csv(input_file: str) -> None:
    rows = [
        "product_id,name,cost,price,category",
        "1,Laptop,850,1200,Electronics",
        "2,Mouse,12,25,Accessories",
        "3,Keyboard,40,75,Accessories",
        "4,Monitor,220,350,Electronics",
        "5,Headphones,90,150,Accessories",
        "6,Webcam,60,110,Electronics",
    ]
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


def main() -> None:
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import avg, col, count, round as spark_round
    except ImportError:
        print("PySpark is not installed.")
        print("Install with: pip install pyspark")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)

    input_file = os.path.join(DATA_DIR, "products_spark_input.csv")
    output_path = os.path.join(DATA_DIR, "products_spark_summary.parquet")

    write_input_csv(input_file)

    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace="spark-example",
        job_name="spark-product-margin-summary",
        job_description="Spark job that computes category-level margin summary",
    )

    spark = (
        SparkSession.builder
        .appName("openlineage-spark-example")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        df_input = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(input_file)
        )

        with tracker.track_run() as run:
            run.add_input(
                name="products_spark_input.csv",
                uri=f"file://{os.path.abspath(input_file)}",
                schema=schema_from_spark_df(df_input),
            )

            df_result = (
                df_input
                .withColumn("margin", col("price") - col("cost"))
                .filter(col("margin") >= 50)
                .groupBy("category")
                .agg(
                    spark_round(avg("margin"), 2).alias("avg_margin"),
                    count("*").alias("product_count"),
                )
                .orderBy("category")
            )

            df_result.write.mode("overwrite").parquet(output_path)

            run.add_output(
                name="products_spark_summary.parquet",
                uri=f"file://{os.path.abspath(output_path)}",
                schema=schema_from_spark_df(df_result),
            )

        print("=" * 68)
        print("Spark Lineage Example Completed")
        print("=" * 68)
        print(f"Input:  {os.path.abspath(input_file)}")
        print(f"Output: {os.path.abspath(output_path)}")
        print("\nView in Marquez UI: http://localhost:3000")
        print("Search for job: spark-product-margin-summary")
        print("Namespace: spark-example")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
