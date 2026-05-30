# Spark Lineage Example

This folder contains a PySpark lineage example:

- spark_lineage_example.py

## Run

1. Start Marquez stack from project root:

```bash
./install-scripts/compose.sh up -d
```

2. Activate Python env and install PySpark:

```bash
cd ../python
source .venv/bin/activate
pip install pyspark
```

3. Run Spark example:

```bash
cd ../spark
python spark_lineage_example.py
```

## Expected Lineage

- Namespace: spark-example
- Job: spark-product-margin-summary
- Input: products_spark_input.csv
- Output: products_spark_summary.parquet
