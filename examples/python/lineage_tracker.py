#!/usr/bin/env python3
"""
Generic OpenLineage Tracker
A reusable module for tracking data lineage in Python pipelines.
"""

import requests
import uuid
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


class LineageTracker:
    """
    A generic lineage tracker for Python data pipelines.
    
    Usage:
        tracker = LineageTracker(
            marquez_url="http://localhost:5050",
            namespace="my-namespace",
            job_name="my-job"
        )
        
        with tracker.track_run() as run:
            run.add_input("input.csv")
            # ... do your processing ...
            run.add_output("output.csv", schema=[...])
    """
    
    def __init__(
        self,
        marquez_url: str = None,
        namespace: str = "default",
        job_name: str = "python-job",
        job_description: str = None
    ):
        """
        Initialize the lineage tracker.
        
        Args:
            marquez_url: Marquez API URL (default: from env or http://localhost:5050)
            namespace: Namespace for jobs and datasets
            job_name: Name of the job
            job_description: Optional job description
        """
        self.marquez_url = marquez_url or os.getenv('MARQUEZ_URL', 'http://localhost:5050')
        self.namespace = namespace
        self.job_name = job_name
        self.job_description = job_description
        self.producer = "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client"
        
    def _send_event(
        self,
        event_type: str,
        run_id: str,
        inputs: List[Dict] = None,
        outputs: List[Dict] = None,
        job_facets: Dict = None
    ) -> requests.Response:
        """Send a lineage event to Marquez."""
        
        # Build job facets
        facets = {}
        if self.job_description:
            facets["documentation"] = {
                "_producer": self.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationJobFacet.json",
                "description": self.job_description
            }
        if job_facets:
            facets.update(job_facets)
        
        event = {
            "eventType": event_type,
            "eventTime": datetime.utcnow().isoformat() + "Z",
            "run": {"runId": run_id},
            "job": {
                "namespace": self.namespace,
                "name": self.job_name,
                "facets": facets
            },
            "inputs": inputs or [],
            "outputs": outputs or [],
            "producer": self.producer,
            "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
        }
        
        try:
            response = requests.post(
                f"{self.marquez_url}/api/v1/lineage",
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to send {event_type} event: {e}")
            return None
    
    @contextmanager
    def track_run(self, run_id: str = None):
        """
        Context manager for tracking a pipeline run.
        
        Usage:
            with tracker.track_run() as run:
                run.add_input("input.csv")
                # ... processing ...
                run.add_output("output.csv")
        """
        run = Run(self, run_id or str(uuid.uuid4()))
        
        try:
            # Send START event
            self._send_event("START", run.run_id, inputs=run.inputs)
            yield run
            # Send COMPLETE event
            self._send_event("COMPLETE", run.run_id, inputs=run.inputs, outputs=run.outputs)
        except Exception as e:
            # Send FAIL event
            self._send_event("FAIL", run.run_id, inputs=run.inputs, outputs=run.outputs)
            raise


class Run:
    """Represents a single pipeline run with inputs and outputs."""
    
    def __init__(self, tracker: LineageTracker, run_id: str):
        self.tracker = tracker
        self.run_id = run_id
        self.inputs: List[Dict] = []
        self.outputs: List[Dict] = []
    
    def add_input(
        self,
        name: str,
        namespace: str = None,
        uri: str = None,
        schema: List[Dict] = None,
        facets: Dict = None
    ):
        """
        Add an input dataset.
        
        Args:
            name: Dataset name (e.g., "input.csv")
            namespace: Dataset namespace (default: same as job)
            uri: Dataset URI (e.g., "file:///path/to/file")
            schema: List of field definitions [{"name": "col1", "type": "VARCHAR"}, ...]
            facets: Additional dataset facets
        """
        dataset = self._build_dataset(name, namespace, uri, schema, facets)
        self.inputs.append(dataset)
        return self
    
    def add_output(
        self,
        name: str,
        namespace: str = None,
        uri: str = None,
        schema: List[Dict] = None,
        facets: Dict = None
    ):
        """
        Add an output dataset.
        
        Args:
            name: Dataset name (e.g., "output.csv")
            namespace: Dataset namespace (default: same as job)
            uri: Dataset URI (e.g., "file:///path/to/file")
            schema: List of field definitions [{"name": "col1", "type": "VARCHAR"}, ...]
            facets: Additional dataset facets
        """
        dataset = self._build_dataset(name, namespace, uri, schema, facets)
        self.outputs.append(dataset)
        return self
    
    def _build_dataset(
        self,
        name: str,
        namespace: str = None,
        uri: str = None,
        schema: List[Dict] = None,
        facets: Dict = None
    ) -> Dict:
        """Build a dataset definition."""
        dataset = {
            "namespace": namespace or self.tracker.namespace,
            "name": name,
            "facets": facets or {}
        }
        
        # Add schema facet if provided
        if schema:
            dataset["facets"]["schema"] = {
                "_producer": self.tracker.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": schema
            }
        
        # Add dataSource facet if URI provided
        if uri:
            dataset["facets"]["dataSource"] = {
                "_producer": self.tracker.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json",
                "name": self._get_datasource_type(uri),
                "uri": uri
            }
        
        return dataset
    
    def _get_datasource_type(self, uri: str) -> str:
        """Infer datasource type from URI."""
        if uri.startswith("file://"):
            return "file"
        elif uri.startswith("s3://"):
            return "s3"
        elif uri.startswith("postgresql://"):
            return "postgresql"
        elif uri.startswith("mysql://"):
            return "mysql"
        else:
            return "unknown"


# Helper functions for common use cases

def infer_schema_from_dataframe(df) -> List[Dict]:
    """
    Infer schema from a pandas DataFrame.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        List of field definitions
    """
    schema = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        
        # Map pandas dtypes to SQL types
        if dtype.startswith('int'):
            sql_type = 'INTEGER'
        elif dtype.startswith('float'):
            sql_type = 'DOUBLE'
        elif dtype == 'bool':
            sql_type = 'BOOLEAN'
        elif dtype == 'datetime64':
            sql_type = 'TIMESTAMP'
        else:
            sql_type = 'VARCHAR'
        
        schema.append({
            "name": col,
            "type": sql_type
        })
    
    return schema


def track_pandas_pipeline(
    tracker: LineageTracker,
    input_file: str,
    output_file: str,
    process_func,
    input_schema: List[Dict] = None,
    output_schema: List[Dict] = None
):
    """
    Helper function to track a simple pandas pipeline.
    
    Args:
        tracker: LineageTracker instance
        input_file: Input file path
        output_file: Output file path
        process_func: Function that takes input_file and returns DataFrame
        input_schema: Optional input schema
        output_schema: Optional output schema
    """
    import pandas as pd
    
    with tracker.track_run() as run:
        # Add input
        run.add_input(
            name=os.path.basename(input_file),
            uri=f"file://{os.path.abspath(input_file)}",
            schema=input_schema
        )
        
        # Process data
        df = process_func(input_file)
        
        # Infer output schema if not provided
        if output_schema is None:
            output_schema = infer_schema_from_dataframe(df)
        
        # Write output
        df.to_csv(output_file, index=False)
        
        # Add output
        run.add_output(
            name=os.path.basename(output_file),
            uri=f"file://{os.path.abspath(output_file)}",
            schema=output_schema
        )
    
    return df


# Example usage
if __name__ == "__main__":
    # Example 1: Basic usage
    tracker = LineageTracker(
        namespace="example",
        job_name="test-job",
        job_description="A test job"
    )
    
    with tracker.track_run() as run:
        run.add_input("input.csv", uri="file:///data/input.csv")
        # ... do processing ...
        run.add_output(
            "output.csv",
            uri="file:///data/output.csv",
            schema=[
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"}
            ]
        )
    
    print("✓ Lineage tracked successfully!")

