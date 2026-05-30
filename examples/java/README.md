# Java Lineage Example

A minimal Java example that emits OpenLineage START and COMPLETE events to Marquez.

## What It Does

- Generates input CSV file: ../../data/products_java.csv
- Filters high-margin products (margin >= 50)
- Writes output CSV file: ../../data/high_margin_products_java.csv
- Sends lineage events for one job:
  - Namespace: java-example
  - Job: java-product-margin-pipeline

## Prerequisites

- Marquez running from project root:

```bash
./install-scripts/compose.sh up -d
```

- Java 11 or later

macOS install (Homebrew):

```bash
brew install openjdk
```

## Run

From this directory:

```bash
javac JavaLineageExample.java
java JavaLineageExample
```

## Verify in Marquez

- Open: http://localhost:3000
- Search for job: java-product-margin-pipeline
- Namespace: java-example

## API Check

```bash
curl http://localhost:5050/api/v1/namespaces/java-example/jobs/java-product-margin-pipeline
```
