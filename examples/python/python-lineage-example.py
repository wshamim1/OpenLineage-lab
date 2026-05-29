#!/usr/bin/env python3
"""
Simple Python Data Pipeline with OpenLineage Tracking
This script demonstrates how to track data lineage for a simple ETL process.
"""

import json
import requests
import pandas as pd
from datetime import datetime
import uuid
import os

# Configuration
MARQUEZ_URL = os.getenv('MARQUEZ_URL', 'http://localhost:5050')
NAMESPACE = 'python-example'
JOB_NAME = 'csv-processor'
DATA_DIR = '../../data'  # Data directory relative to script location

def send_lineage_event(event_type, run_id, inputs=None, outputs=None):
    """Send a lineage event to Marquez/OpenLineage"""
    
    event = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "run": {
            "runId": run_id
        },
        "job": {
            "namespace": NAMESPACE,
            "name": JOB_NAME,
            "facets": {
                "documentation": {
                    "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationJobFacet.json",
                    "description": "A simple CSV processing job that reads customer data, filters it, and writes results"
                }
            }
        },
        "inputs": inputs or [],
        "outputs": outputs or [],
        "producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
    }
    
    response = requests.post(
        f"{MARQUEZ_URL}/api/v1/lineage",
        json=event,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        print(f"✓ {event_type} event sent successfully")
    else:
        print(f"✗ Failed to send {event_type} event: {response.status_code}")
        print(response.text)
    
    return response

def create_sample_data():
    """Create a sample CSV file for demonstration"""
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    data = {
        'customer_id': [1, 2, 3, 4, 5],
        'name': ['Alice Johnson', 'Bob Smith', 'Carol White', 'David Brown', 'Eve Davis'],
        'email': ['alice@example.com', 'bob@example.com', 'carol@example.com', 'david@example.com', 'eve@example.com'],
        'age': [28, 35, 42, 31, 29],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    }
    
    df = pd.DataFrame(data)
    output_path = os.path.join(DATA_DIR, 'customers.csv')
    df.to_csv(output_path, index=False)
    print(f"✓ Created sample data: {output_path}")
    return df

def process_data():
    """Main data processing pipeline with lineage tracking"""
    
    # Generate unique run ID
    run_id = str(uuid.uuid4())
    print(f"\n{'='*60}")
    print(f"Starting Data Pipeline")
    print(f"Run ID: {run_id}")
    print(f"Marquez URL: {MARQUEZ_URL}")
    print(f"{'='*60}\n")
    
    # Define input dataset
    input_file = 'customers.csv'
    input_path = os.path.join(DATA_DIR, input_file)
    input_dataset = {
        "namespace": NAMESPACE,
        "name": input_file,
        "facets": {
            "dataSource": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json",
                "name": "file",
                "uri": f"file://{input_path}"
            }
        }
    }
    
    # Send START event
    print("Step 1: Sending START event...")
    send_lineage_event("START", run_id, inputs=[input_dataset])
    
    # Create sample data
    print("\nStep 2: Creating sample data...")
    df = create_sample_data()
    
    # Process data
    print("\nStep 3: Processing data...")
    print(f"  - Read {len(df)} records")
    
    # Filter customers over 30
    filtered_df = df[df['age'] > 30]
    print(f"  - Filtered to {len(filtered_df)} customers over 30")
    
    # Add a new column
    filtered_df['status'] = 'active'
    print(f"  - Added 'status' column")
    
    # Write output
    output_file = 'customers_filtered.csv'
    output_path = os.path.join(DATA_DIR, output_file)
    filtered_df.to_csv(output_path, index=False)
    print(f"  - Wrote results to {output_path}")
    
    # Define output dataset with schema
    output_dataset = {
        "namespace": NAMESPACE,
        "name": output_file,
        "facets": {
            "schema": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": [
                    {"name": "customer_id", "type": "INTEGER", "description": "Unique customer identifier"},
                    {"name": "name", "type": "VARCHAR", "description": "Customer full name"},
                    {"name": "email", "type": "VARCHAR", "description": "Customer email address"},
                    {"name": "age", "type": "INTEGER", "description": "Customer age"},
                    {"name": "city", "type": "VARCHAR", "description": "Customer city"},
                    {"name": "status", "type": "VARCHAR", "description": "Customer status"}
                ]
            },
            "dataSource": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json",
                "name": "file",
                "uri": f"file://{output_path}"
            }
        }
    }
    
    # Send COMPLETE event
    print("\nStep 4: Sending COMPLETE event...")
    send_lineage_event("COMPLETE", run_id, inputs=[input_dataset], outputs=[output_dataset])
    
    print(f"\n{'='*60}")
    print("Pipeline Completed Successfully!")
    print(f"{'='*60}\n")
    
    print("View your lineage in Marquez:")
    print(f"  Web UI: http://localhost:3000")
    print(f"  Search for: {JOB_NAME}")
    print(f"\nAPI Endpoints:")
    print(f"  Job: {MARQUEZ_URL}/api/v1/namespaces/{NAMESPACE}/jobs/{JOB_NAME}")
    print(f"  Run: {MARQUEZ_URL}/api/v1/namespaces/{NAMESPACE}/jobs/{JOB_NAME}/runs/{run_id}")
    print(f"\nDatasets:")
    print(f"  Input:  customers.csv ({len(df)} records)")
    print(f"  Output: {output_file} ({len(filtered_df)} records)")

if __name__ == "__main__":
    try:
        process_data()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

