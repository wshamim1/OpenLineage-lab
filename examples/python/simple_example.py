#!/usr/bin/env python3
"""
Simple example using the generic LineageTracker.
This shows how easy it is to add lineage tracking to any Python script.
"""

import pandas as pd
from lineage_tracker import LineageTracker, infer_schema_from_dataframe
import os

# Configuration
DATA_DIR = '../../data'
MARQUEZ_URL = os.getenv('MARQUEZ_URL', 'http://localhost:5050')

def main():
    # Create a lineage tracker
    tracker = LineageTracker(
        marquez_url=MARQUEZ_URL,
        namespace="simple-example",
        job_name="data-processor",
        job_description="A simple data processing job using the generic tracker"
    )
    
    print("=" * 60)
    print("Simple Lineage Tracking Example")
    print("=" * 60)
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample data
    input_file = os.path.join(DATA_DIR, 'products.csv')
    output_file = os.path.join(DATA_DIR, 'expensive_products.csv')
    
    # Create sample product data
    products_data = {
        'product_id': [1, 2, 3, 4, 5],
        'name': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones'],
        'price': [1200, 25, 75, 350, 150],
        'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Accessories']
    }
    df_input = pd.DataFrame(products_data)
    df_input.to_csv(input_file, index=False)
    print(f"\n✓ Created input data: {input_file}")
    print(f"  Records: {len(df_input)}")
    
    # Track the pipeline run
    with tracker.track_run() as run:
        print("\n✓ Started lineage tracking")
        
        # Add input dataset with schema
        input_schema = infer_schema_from_dataframe(df_input)
        run.add_input(
            name='products.csv',
            uri=f"file://{os.path.abspath(input_file)}",
            schema=input_schema
        )
        print("  - Tracked input dataset")
        
        # Process data: filter expensive products (price > 100)
        df = pd.read_csv(input_file)
        df_filtered = df[df['price'] > 100].copy()
        print(f"\n✓ Processed data")
        print(f"  - Filtered {len(df)} products to {len(df_filtered)} expensive products")
        
        # Write output
        df_filtered.to_csv(output_file, index=False)
        print(f"  - Wrote output: {output_file}")
        
        # Add output dataset with schema
        output_schema = infer_schema_from_dataframe(df_filtered)
        run.add_output(
            name='expensive_products.csv',
            uri=f"file://{os.path.abspath(output_file)}",
            schema=output_schema
        )
        print("  - Tracked output dataset")
    
    print("\n✓ Lineage tracking completed")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Input:  {len(df_input)} products")
    print(f"Output: {len(df_filtered)} expensive products (price > $100)")
    print(f"\nExpensive products:")
    for _, row in df_filtered.iterrows():
        print(f"  - {row['name']}: ${row['price']}")
    
    print("\n" + "=" * 60)
    print("View Lineage in Marquez")
    print("=" * 60)
    print(f"Web UI: http://localhost:3000")
    print(f"Search for: data-processor")
    print(f"Namespace: simple-example")
    print("=" * 60)

if __name__ == "__main__":
    main()
