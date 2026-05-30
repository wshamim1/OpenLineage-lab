#!/usr/bin/env python3
"""
Multi-stage example using the generic LineageTracker.

This script creates a small 3-stage pipeline so lineage shows a richer graph:
1) ingest-products: seed and write raw product data
2) clean-products: standardize and validate product records
3) build-product-marts: create filtered and aggregated outputs
"""

import os
import pandas as pd

from lineage_tracker import LineageTracker, infer_schema_from_dataframe


DATA_DIR = "../../data"
MARQUEZ_URL = os.getenv("MARQUEZ_URL", "http://localhost:5050")
NAMESPACE = "multi-stage-example"


def stage_1_ingest() -> str:
    """Create and write raw input dataset."""
    raw_file = os.path.join(DATA_DIR, "products_raw.csv")

    raw_data = {
        "product_id": [1, 2, 3, 4, 5, 6],
        "name": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones", "Webcam"],
        "price": [1200, 25, 75, 350, 150, 110],
        "category": ["Electronics", "Accessories", "Accessories", "Electronics", "Accessories", "Electronics"],
        "stock": [8, 120, 80, 22, 45, 60],
    }
    df_raw = pd.DataFrame(raw_data)
    df_raw.to_csv(raw_file, index=False)

    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace=NAMESPACE,
        job_name="ingest-products",
        job_description="Generate and persist raw product data",
    )

    with tracker.track_run() as run:
        run.add_output(
            name="products_raw.csv",
            uri=f"file://{os.path.abspath(raw_file)}",
            schema=infer_schema_from_dataframe(df_raw),
        )

    print(f"\n[Stage 1] Wrote raw dataset: {raw_file} ({len(df_raw)} rows)")
    return raw_file


def stage_2_clean(raw_file: str) -> str:
    """Clean and standardize raw data."""
    clean_file = os.path.join(DATA_DIR, "products_clean.csv")

    df_raw = pd.read_csv(raw_file)
    df_clean = df_raw.copy()
    df_clean["name"] = df_clean["name"].str.strip()
    df_clean["category"] = df_clean["category"].str.lower()
    df_clean = df_clean[df_clean["price"] > 0].reset_index(drop=True)
    df_clean.to_csv(clean_file, index=False)

    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace=NAMESPACE,
        job_name="clean-products",
        job_description="Standardize and validate raw products",
    )

    with tracker.track_run() as run:
        run.add_input(
            name="products_raw.csv",
            uri=f"file://{os.path.abspath(raw_file)}",
            schema=infer_schema_from_dataframe(df_raw),
        )
        run.add_output(
            name="products_clean.csv",
            uri=f"file://{os.path.abspath(clean_file)}",
            schema=infer_schema_from_dataframe(df_clean),
        )

    print(f"[Stage 2] Wrote cleaned dataset: {clean_file} ({len(df_clean)} rows)")
    return clean_file


def stage_3_build_marts(clean_file: str) -> tuple[str, str]:
    """Build marts: expensive products and category summary."""
    expensive_file = os.path.join(DATA_DIR, "expensive_products.csv")
    summary_file = os.path.join(DATA_DIR, "category_summary.csv")

    df_clean = pd.read_csv(clean_file)

    df_expensive = df_clean[df_clean["price"] >= 100].copy()
    df_expensive["price_tier"] = "premium"
    df_expensive.to_csv(expensive_file, index=False)

    df_summary = (
        df_clean.groupby("category", as_index=False)
        .agg(product_count=("product_id", "count"), avg_price=("price", "mean"), total_stock=("stock", "sum"))
        .sort_values("category")
    )
    df_summary["avg_price"] = df_summary["avg_price"].round(2)
    df_summary.to_csv(summary_file, index=False)

    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace=NAMESPACE,
        job_name="build-product-marts",
        job_description="Create curated output datasets for analytics",
    )

    with tracker.track_run() as run:
        run.add_input(
            name="products_clean.csv",
            uri=f"file://{os.path.abspath(clean_file)}",
            schema=infer_schema_from_dataframe(df_clean),
        )
        run.add_output(
            name="expensive_products.csv",
            uri=f"file://{os.path.abspath(expensive_file)}",
            schema=infer_schema_from_dataframe(df_expensive),
        )
        run.add_output(
            name="category_summary.csv",
            uri=f"file://{os.path.abspath(summary_file)}",
            schema=infer_schema_from_dataframe(df_summary),
        )

    print(f"[Stage 3] Wrote mart dataset: {expensive_file} ({len(df_expensive)} rows)")
    print(f"[Stage 3] Wrote mart dataset: {summary_file} ({len(df_summary)} rows)")

    return expensive_file, summary_file


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=" * 68)
    print("Multi-Stage Lineage Tracking Example")
    print("=" * 68)

    raw_file = stage_1_ingest()
    clean_file = stage_2_clean(raw_file)
    expensive_file, summary_file = stage_3_build_marts(clean_file)

    print("\n" + "=" * 68)
    print("Pipeline Summary")
    print("=" * 68)
    print("Jobs tracked in namespace: multi-stage-example")
    print("  1. ingest-products")
    print("  2. clean-products")
    print("  3. build-product-marts")
    print("\nDatasets produced:")
    print(f"  - {raw_file}")
    print(f"  - {clean_file}")
    print(f"  - {expensive_file}")
    print(f"  - {summary_file}")
    print("\nView in Marquez UI: http://localhost:3000")
    print("Search for jobs in namespace: multi-stage-example")


if __name__ == "__main__":
    main()
