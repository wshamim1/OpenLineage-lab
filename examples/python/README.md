# Python Lineage Examples

Python examples demonstrating how to track data lineage with OpenLineage and Marquez.

## 📋 Prerequisites

1. **Marquez services running**
   ```bash
   cd ../..
    ./install-scripts/compose.sh up -d
   ```

2. **Python 3.7+** installed

3. **Dependencies installed**
   ```bash
   pip3 install -r requirements.txt
   ```

## 🚀 Quick Start

### Option 1: Use the Generic Tracker (Recommended)

```bash
# Run the simple example
python3 simple_example.py

# Run the multi-stage pipeline example
python3 multi_stage_example.py

# Or run the database example
python3 database_example.py
```

### Option 2: Complete Example

```bash
# Run the full CSV processing example
python3 python-lineage-example.py
```

## 📁 Files

### Generic Tracker (Reusable)
- **`lineage_tracker.py`** - 🎯 **Generic lineage tracker module** - Use this in your own code!

### Examples
- **`simple_example.py`** - Simple example using the generic tracker
- **`multi_stage_example.py`** - Multi-stage pipeline with intermediate datasets and two marts
- **`database_example.py`** - Database/S3 example using the generic tracker
- **`python-lineage-example.py`** - Complete CSV processing example (standalone)

### Configuration
- **`requirements.txt`** - Python dependencies (pandas, requests)
- **`README.md`** - This file

## 🎯 What the Example Does

The `python-lineage-example.py` script demonstrates a simple ETL pipeline:

1. **Creates sample data** - 5 customer records
2. **Filters data** - Customers over 30 years old
3. **Transforms data** - Adds a 'status' column
4. **Writes output** - Filtered results to CSV
5. **Tracks lineage** - Sends START and COMPLETE events to Marquez

### Input Data (customers.csv)
```csv
customer_id,name,email,age,city
1,Alice Johnson,alice@example.com,28,New York
2,Bob Smith,bob@example.com,35,Los Angeles
3,Carol White,carol@example.com,42,Chicago
4,David Brown,david@example.com,31,Houston
5,Eve Davis,eve@example.com,29,Phoenix
```

### Output Data (customers_filtered.csv)
```csv
customer_id,name,email,age,city,status
2,Bob Smith,bob@example.com,35,Los Angeles,active
3,Carol White,carol@example.com,42,Chicago,active
4,David Brown,david@example.com,31,Houston,active
```

## 📊 Lineage Tracked

The example tracks:
- **Job**: `csv-processor` in namespace `python-example`
- **Input Dataset**: `customers.csv` (5 records)
- **Output Dataset**: `customers_filtered.csv` (3 records) with schema
- **Run Metadata**: Unique run ID, timestamps, duration

## 🔍 View Results

### Web UI
1. Open http://localhost:3000
2. Search for `csv-processor`
3. View the lineage graph:
   - Input: customers.csv
   - Job: csv-processor
   - Output: customers_filtered.csv (with schema)

### API
```bash
# Get job details
curl http://localhost:5050/api/v1/namespaces/python-example/jobs/csv-processor | jq

# Get output dataset with schema
curl http://localhost:5050/api/v1/namespaces/python-example/datasets/customers_filtered.csv | jq
```

## 🛠️ Customizing for Your Pipeline

### Basic Template
```python
import requests
import uuid
from datetime import datetime

MARQUEZ_URL = 'http://localhost:5050'
NAMESPACE = 'your-namespace'
JOB_NAME = 'your-job'

def send_lineage_event(event_type, run_id, inputs=None, outputs=None):
    event = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "run": {"runId": run_id},
        "job": {"namespace": NAMESPACE, "name": JOB_NAME},
        "inputs": inputs or [],
        "outputs": outputs or [],
        "producer": "your-producer",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
    }
    requests.post(f"{MARQUEZ_URL}/api/v1/lineage", json=event)

# Your pipeline
run_id = str(uuid.uuid4())
send_lineage_event("START", run_id, inputs=[...])
# ... do your processing ...
send_lineage_event("COMPLETE", run_id, inputs=[...], outputs=[...])
```

## 📚 Documentation

For detailed documentation, see:
- [Python Lineage Guide](../../docs/PYTHON_LINEAGE_GUIDE.md)

## 🔗 Resources

- [OpenLineage Python Client](https://github.com/OpenLineage/OpenLineage/tree/main/client/python)
- [OpenLineage Specification](https://openlineage.io/spec/)
- [Marquez API Documentation](https://marquezproject.github.io/marquez/openapi.html)

---

**Made with Bob** 🤖
## 🎯 Using the Generic Tracker in Your Code

The `lineage_tracker.py` module provides a simple, reusable way to add lineage tracking to any Python script.

### Basic Usage

```python
from lineage_tracker import LineageTracker

# Create a tracker
tracker = LineageTracker(
    namespace="my-namespace",
    job_name="my-job",
    job_description="What this job does"
)

# Track a pipeline run
with tracker.track_run() as run:
    # Add input datasets
    run.add_input("input.csv", uri="file:///path/to/input.csv")
    
    # ... do your processing ...
    
    # Add output datasets with schema
    run.add_output(
        "output.csv",
        uri="file:///path/to/output.csv",
        schema=[
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"}
        ]
    )
```

### Features

✅ **Context Manager** - Automatically sends START and COMPLETE events  
✅ **Error Handling** - Sends FAIL event if exception occurs  
✅ **Schema Inference** - Auto-detect schema from pandas DataFrames  
✅ **Multiple Inputs/Outputs** - Track complex pipelines  
✅ **Flexible URIs** - Support for files, databases, S3, etc.

### Advanced Usage

#### With Pandas DataFrames

```python
from lineage_tracker import LineageTracker, infer_schema_from_dataframe
import pandas as pd

tracker = LineageTracker(namespace="analytics", job_name="report-generator")

with tracker.track_run() as run:
    # Read data
    df = pd.read_csv("sales.csv")
    
    # Auto-infer schema
    schema = infer_schema_from_dataframe(df)
    run.add_input("sales.csv", schema=schema)
    
    # Process
    df_summary = df.groupby('region')['revenue'].sum()
    
    # Track output
    run.add_output("summary.csv", schema=infer_schema_from_dataframe(df_summary))
```

#### Database Operations

```python
tracker = LineageTracker(namespace="etl", job_name="db-sync")

with tracker.track_run() as run:
    # Track database input
    run.add_input(
        name="users_table",
        namespace="source-db",
        uri="postgresql://host:5432/db/users",
        schema=[
            {"name": "user_id", "type": "INTEGER"},
            {"name": "email", "type": "VARCHAR"}
        ]
    )
    
    # Track S3 output
    run.add_output(
        name="users.parquet",
        namespace="data-lake",
        uri="s3://bucket/data/users.parquet"
    )
```

#### Multiple Inputs and Outputs

```python
with tracker.track_run() as run:
    # Multiple inputs
    run.add_input("customers.csv")
    run.add_input("orders.csv")
    run.add_input("products.csv")
    
    # ... join and process ...
    
    # Multiple outputs
    run.add_output("customer_orders.csv")
    run.add_output("order_summary.csv")
```
