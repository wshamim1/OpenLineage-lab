#!/usr/bin/env python3
"""
Database example using the generic LineageTracker.
Shows how to track lineage for database operations.
"""

from lineage_tracker import LineageTracker
import os

# Configuration
MARQUEZ_URL = os.getenv('MARQUEZ_URL', 'http://localhost:5050')

def main():
    """
    Example showing how to track database operations.
    This is a mock example - adapt for your actual database.
    """
    
    # Create a lineage tracker
    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace="database-example",
        job_name="etl-pipeline",
        job_description="ETL pipeline that reads from PostgreSQL and writes to S3"
    )
    
    print("=" * 60)
    print("Database Lineage Tracking Example")
    print("=" * 60)
    
    # Track the pipeline run
    with tracker.track_run() as run:
        print("\n✓ Started lineage tracking")
        
        # Add database input
        run.add_input(
            name="customers_table",
            namespace="production-db",
            uri="postgresql://localhost:5432/mydb/customers",
            schema=[
                {"name": "customer_id", "type": "INTEGER", "description": "Primary key"},
                {"name": "name", "type": "VARCHAR", "description": "Customer name"},
                {"name": "email", "type": "VARCHAR", "description": "Email address"},
                {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
            ]
        )
        print("  - Tracked input: PostgreSQL table")
        
        # Simulate processing
        print("\n✓ Processing data...")
        print("  - Reading from PostgreSQL")
        print("  - Transforming data")
        print("  - Aggregating metrics")
        
        # Add S3 output
        run.add_output(
            name="customer_summary.parquet",
            namespace="data-lake",
            uri="s3://my-bucket/data/customer_summary.parquet",
            schema=[
                {"name": "customer_id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "total_orders", "type": "INTEGER"},
                {"name": "total_spent", "type": "DOUBLE"},
                {"name": "last_order_date", "type": "TIMESTAMP"}
            ]
        )
        print("  - Tracked output: S3 parquet file")
    
    print("\n✓ Lineage tracking completed")
    
    print("\n" + "=" * 60)
    print("View Lineage in Marquez")
    print("=" * 60)
    print(f"Web UI: http://localhost:3000")
    print(f"Search for: etl-pipeline")
    print(f"Namespace: database-example")
    print("\nYou'll see:")
    print("  Input:  PostgreSQL table (production-db.customers_table)")
    print("  Job:    etl-pipeline")
    print("  Output: S3 parquet file (data-lake.customer_summary.parquet)")
    print("=" * 60)

if __name__ == "__main__":
    main()


