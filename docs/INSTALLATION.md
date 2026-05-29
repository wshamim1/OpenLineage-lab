# OpenLineage with Podman - Getting Started Guide

This guide covers how to quickly get started collecting dataset, job, and run metadata using OpenLineage with **Podman** instead of Docker. We'll show how to collect run-level metadata as OpenLineage events using Marquez as the HTTP backend, then explore lineage metadata via the Marquez UI.

## Prerequisites

Before you begin, make sure you have installed:

- **Podman 4.0+** - Container runtime (Docker alternative)
- **podman-compose** (optional but recommended) - For easier container orchestration
- **curl** - For testing API endpoints

### Installing Podman

#### macOS
```bash
brew install podman
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install podman
```

#### Linux (RHEL/Fedora/CentOS)
```bash
sudo dnf install podman
```

### Installing podman-compose (Optional but Recommended)

```bash
pip3 install podman-compose
```

Or using pipx:
```bash
pipx install podman-compose
```

## Quick Start

### 1. Initialize Podman (macOS only)

On macOS, you need to initialize and start the Podman machine:

```bash
podman machine init
podman machine start
```

The startup script will do this automatically if needed.

### 2. Start Marquez with Podman

Navigate to the OpenLineage directory and run the startup script:

```bash
cd OpenLineage
chmod +x podman-up.sh podman-down.sh
./podman-up.sh
```

**Note for macOS users:** Port 5000 is reserved by AirPlay Receiver. If you encounter port conflicts, use:

```bash
./podman-up.sh --api-port 9000
```

This will configure the API to listen on port 9000 instead. Remember to update the URLs in the examples below with the appropriate port number.

#### Script Options

- `--api-port PORT` - Set custom API port (default: 5000)
- `--tag VERSION` - Use specific image version (default: latest)
- `--help` - Show help message

### 3. Verify Services are Running

The script will start three services:

- **Marquez UI**: http://localhost:3000
- **Marquez API**: http://localhost:5000 (or your custom port)
- **PostgreSQL**: localhost:5432

To verify all containers are running:

```bash
podman ps
```

You should see three containers:
- `marquez-web`
- `marquez-api`
- `marquez-db`

### 4. View Logs

**With podman-compose:**
```bash
podman-compose logs -f
```

**Without podman-compose:**
```bash
podman logs -f marquez-api
podman logs -f marquez-web
podman logs -f marquez-db
```

## Collect Run-Level Metadata

Now let's collect some lineage metadata! We'll create a simple job with input and output datasets.

### Step 1: Start a Run

Create a new job run with an input dataset:

```bash
curl -X POST http://localhost:5000/api/v1/lineage \
  -i -H 'Content-Type: application/json' \
  -d '{
        "eventType": "START",
        "eventTime": "2020-12-28T19:52:00.001+10:00",
        "run": {
          "runId": "0176a8c2-fe01-7439-87e6-56a1a1b4029f"
        },
        "job": {
          "namespace": "my-namespace",
          "name": "my-job"
        },
        "inputs": [{
          "namespace": "my-namespace",
          "name": "my-input"
        }],  
        "producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
      }'
```

**Expected Response:** `201 CREATED`

### Step 2: Complete a Run

Mark the run as complete with an output dataset and schema:

```bash
curl -X POST http://localhost:5000/api/v1/lineage \
  -i -H 'Content-Type: application/json' \
  -d '{
        "eventType": "COMPLETE",
        "eventTime": "2020-12-28T20:52:00.001+10:00",
        "run": {
          "runId": "0176a8c2-fe01-7439-87e6-56a1a1b4029f"
        },
        "job": {
          "namespace": "my-namespace",
          "name": "my-job"
        },
        "outputs": [{
          "namespace": "my-namespace",
          "name": "my-output",
          "facets": {
            "schema": {
              "_producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
              "_schemaURL": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/spec/OpenLineage.json#/definitions/SchemaDatasetFacet",
              "fields": [
                { "name": "a", "type": "VARCHAR"},
                { "name": "b", "type": "VARCHAR"}
              ]
            }
          }
        }],     
        "producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
      }'
```

**Expected Response:** `201 CREATED`

## View Collected Lineage Metadata

### 1. Open the Marquez UI

Navigate to http://localhost:3000 in your web browser.

### 2. Search for Your Job

Use the search bar in the upper right corner and search for `my-job`. Click on the job from the dropdown list.

### 3. Explore the Lineage Graph

You should see:
- Job name: `my-job`
- Input dataset: `my-input`
- Output dataset: `my-output`
- Run status: `COMPLETED`

### 4. View Dataset Schema

Click on the `my-output` dataset to see:
- Dataset name
- Column names (a, b)
- Data types (VARCHAR)
- Other metadata

## Using the Test Script

A convenience script is provided to test the setup:

```bash
chmod +x test-lineage.sh
./test-lineage.sh
```

This script will:
1. Check if services are running
2. Send START and COMPLETE events
3. Verify the data was recorded
4. Provide links to view in the UI

## Managing Services

### Stop Services

```bash
./podman-down.sh
```

### Restart Services

```bash
./podman-down.sh
./podman-up.sh
```

### Remove All Data (Clean Start)

```bash
./podman-down.sh
podman volume rm marquez-db-data
podman network rm marquez-network
./podman-up.sh
```

### Check Service Status

```bash
podman ps
```

### View Resource Usage

```bash
podman stats
```

## Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

1. **For API port 5000 (macOS AirPlay conflict):**
   ```bash
   ./podman-up.sh --api-port 9000
   ```

2. **For other ports, find what's using them:**
   ```bash
   lsof -i :5000  # Check port 5000
   lsof -i :3000  # Check port 3000
   ```

### Podman Machine Not Running (macOS)

```bash
podman machine start
```

### Services Not Starting

Check logs for errors:
```bash
podman logs marquez-api
podman logs marquez-db
```

### Database Connection Issues

Ensure PostgreSQL is healthy:
```bash
podman exec -it marquez-db pg_isready -U marquez
```

### Reset Everything

```bash
./podman-down.sh
podman volume rm marquez-db-data
podman network rm marquez-network
podman system prune -a
./podman-up.sh
```

## Differences from Docker

This setup uses Podman instead of Docker. Key differences:

1. **Rootless by default** - Podman runs without root privileges
2. **No daemon** - Podman doesn't require a background service
3. **Pod support** - Native Kubernetes-style pod support
4. **Compatible** - Uses the same container images as Docker
5. **macOS requires VM** - Podman machine provides Linux VM on macOS

## Architecture

```
┌─────────────────────────────────────────┐
│         Marquez Web UI (Port 3000)      │
│         Frontend Application            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Marquez API (Port 5000/9000)       │
│      OpenLineage HTTP Backend           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      PostgreSQL (Port 5432)             │
│      Metadata Storage                   │
└─────────────────────────────────────────┘
```

## Next Steps

- Explore the [test-lineage.sh](./test-lineage.sh) script for more examples
- Check out the [Marquez documentation](https://marquezproject.github.io/marquez/)
- Learn about [OpenLineage specification](https://openlineage.io/)
- Integrate with your data pipelines (Airflow, Spark, dbt, etc.)

## Additional Resources

- [OpenLineage Documentation](https://openlineage.io/docs/)
- [Marquez Project](https://marquezproject.github.io/marquez/)
- [Podman Documentation](https://docs.podman.io/)
- [OpenLineage Slack Community](https://bit.ly/lineageslack)

## Support

For issues or questions:
- OpenLineage Slack: https://bit.ly/lineageslack
- Marquez GitHub: https://github.com/MarquezProject/marquez
- Podman GitHub: https://github.com/containers/podman