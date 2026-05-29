# Python Lineage Tracking Guide

This guide shows how to track data lineage for Python data pipelines using OpenLineage and Marquez.

## Overview

The `python-lineage-example.py` script demonstrates a simple ETL pipeline that:
1. Reads customer data from a CSV file
2. Filters customers over 30 years old
3. Adds a status column
4. Writes the results to a new CSV file
5. **Tracks all lineage metadata** in Marquez

## Prerequisites

1. **Marquez services running** (see main README.md)
2. **Python 3.7+** installed
3. **Required packages** installed

## Installation

```bash
# Install Python dependencies
pip3 install -r requirements.txt
```

## Running the Example

```bash
# Make sure Marquez is running first
./podman-up.sh --api-port 5050

# Run the Python lineage example
python3 python-lineage-example.py
```

## What the Script Does

### 1. Data Processing
- Creates sample customer data (5 records)
- Filters customers over 30 years old (3 records)
- Adds a 'status' column
- Writes filtered results to `customers_filtered.csv`

### 2. Lineage Tracking
The script sends OpenLineage events to Marquez:

**START Event** - When the job begins:
```python
{
  "eventType": "START",
  "job": {
    "namespace": "python-example",
    "name": "csv-processor"
  },
  "inputs": [
    {"namespace": "python-example", "name": "customers.csv"}
  ]
}
```

**COMPLETE Event** - When the job finishes:
```python
{
  "eventType": "COMPLETE",
  "job": {
    "namespace": "python-example",
    "name": "csv-processor"
  },
  "inputs": [
    {"namespace": "python-example", "name": "customers.csv"}
  ],
  "outputs": [
    {
      "namespace": "python-example",
      "name": "customers_filtered.csv",
      "facets": {
        "schema": {
          "fields": [
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"},
            {"name": "email", "type": "VARCHAR"},
            {"name": "age", "type": "INTEGER"},
            {"name": "city", "type": "VARCHAR"},
            {"name": "status", "type": "VARCHAR"}
          ]
        }
      }
    }
  ]
}
```

## Viewing the Lineage

### Web UI
1. Open http://localhost:3000
2. Search for `csv-processor`
3. View the lineage graph showing:
   - **Input**: customers.csv
   - **Job**: csv-processor
   - **Output**: customers_filtered.csv (with schema)

### API
```bash
# Get job details
curl http://localhost:5050/api/v1/namespaces/python-example/jobs/csv-processor | jq

# Get dataset details
curl http://localhost:5050/api/v1/namespaces/python-example/datasets/customers_filtered.csv | jq
```

## Key Concepts

### 1. Run ID
Each execution gets a unique UUID:
```python
run_id = str(uuid.uuid4())
```

### 2. Namespace
Logical grouping for jobs and datasets:
```python
NAMESPACE = 'python-example'
```

### 3. Dataset Facets
Additional metadata about datasets:
- **Schema**: Column names and types
- **DataSource**: Where the data comes from (file, database, etc.)
- **Documentation**: Descriptions and context

### 4. Job Facets
Additional metadata about jobs:
- **Documentation**: Job description and purpose
- **SourceCode**: Link to source code repository
- **SQL**: SQL queries (for SQL-based jobs)

## Customizing for Your Pipeline

### Basic Template
```python
import requests
import uuid
from datetime import datetime

MARQUEZ_URL = 'http://localhost:5050'
NAMESPACE = 'your-namespace'
JOB_NAME = 'your-job-name'

def send_lineage_event(event_type, run_id, inputs=None, outputs=None):
    event = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "run": {"runId": run_id},
        "job": {
            "namespace": NAMESPACE,
            "name": JOB_NAME
        },
        "inputs": inputs or [],
        "outputs": outputs or [],
        "producer": "your-producer-url",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
    }
    
    requests.post(f"{MARQUEZ_URL}/api/v1/lineage", json=event)

# Your pipeline code
run_id = str(uuid.uuid4())

# Send START event
send_lineage_event("START", run_id, inputs=[...])

# Do your data processing
# ...

# Send COMPLETE event
send_lineage_event("COMPLETE", run_id, inputs=[...], outputs=[...])
```

### Adding Schema Information
```python
output_dataset = {
    "namespace": NAMESPACE,
    "name": "output.csv",
    "facets": {
        "schema": {
            "_producer": "your-producer",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": [
                {"name": "column1", "type": "VARCHAR", "description": "Description"},
                {"name": "column2", "type": "INTEGER", "description": "Description"}
            ]
        }
    }
}
```

## Integration with Popular Tools

### Pandas
```python
import pandas as pd

# Read data
df = pd.read_csv('input.csv')

# Track input dataset
input_dataset = {
    "namespace": NAMESPACE,
    "name": "input.csv",
    "facets": {
        "schema": {
            "fields": [
                {"name": col, "type": str(df[col].dtype)}
                for col in df.columns
            ]
        }
    }
}
```

### SQLAlchemy
```python
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/db')

# Track database as input
input_dataset = {
    "namespace": NAMESPACE,
    "name": "database.table_name",
    "facets": {
        "dataSource": {
            "name": "postgresql",
            "uri": "postgresql://localhost/db"
        }
    }
}
```

### Apache Spark
For Spark, use the official OpenLineage Spark integration:
```bash
pip install openlineage-spark
```

## Troubleshooting

### Connection Refused
```
Error: Connection refused
```
**Solution**: Make sure Marquez is running:
```bash
./podman-up.sh --api-port 5050
```

### Wrong Port
```
Error: Failed to send event: 404
```
**Solution**: Check the port in your .env file:
```bash
cat .env | grep API_PORT
```

### Missing Dependencies
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution**: Install requirements:
```bash
pip3 install -r requirements.txt
```

## Best Practices

1. **Always send START and COMPLETE events** - This tracks job execution time
2. **Include schema information** - Helps with data discovery and understanding
3. **Use meaningful namespaces** - Group related jobs and datasets
4. **Add descriptions** - Document what your jobs and datasets do
5. **Handle failures** - Send FAIL events when jobs fail
6. **Use consistent naming** - Makes it easier to find and track lineage

## Example: Handling Failures
```python
try:
    # Send START event
    send_lineage_event("START", run_id, inputs=[...])
    
    # Your processing code
    process_data()
    
    # Send COMPLETE event
    send_lineage_event("COMPLETE", run_id, inputs=[...], outputs=[...])
    
except Exception as e:
    # Send FAIL event
    send_lineage_event("FAIL", run_id, inputs=[...])
    raise
```

## Resources

- [OpenLineage Specification](https://openlineage.io/spec/)
- [Marquez Documentation](https://marquezproject.github.io/marquez/)
- [OpenLineage Python Client](https://github.com/OpenLineage/OpenLineage/tree/main/client/python)

## Next Steps

1. Try modifying the example script for your own data pipeline
2. Add more complex transformations and track them
3. Integrate with your existing Python ETL jobs
4. Explore the Marquez Web UI to visualize your lineage graphs
5. Use the OpenLineage Python client library for more advanced features

---

**Made with Bob** 🤖