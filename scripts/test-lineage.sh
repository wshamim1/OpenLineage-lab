#!/bin/bash

# OpenLineage Test Script
# This script tests the Marquez/OpenLineage setup by sending sample events

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
API_PORT=${API_PORT:-5050}
API_URL="http://localhost:${API_PORT}"
WEB_PORT=${WEB_PORT:-3000}
WEB_URL="http://localhost:${WEB_PORT}"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   OpenLineage/Marquez Test Script         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"

if ! curl -s -f "${API_URL}/api/v1/namespaces" > /dev/null 2>&1; then
    echo -e "${RED}✗ Marquez API is not responding at ${API_URL}${NC}"
    echo "Please start the services first:"
    echo "  ./podman-up.sh"
    exit 1
fi

echo -e "${GREEN}✓ Marquez API is running${NC}"
echo ""

# Generate a unique run ID (UUIDv4 format)
RUN_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

echo -e "${BLUE}Test Configuration:${NC}"
echo "  Run ID: ${RUN_ID}"
echo "  Timestamp: ${TIMESTAMP}"
echo "  API URL: ${API_URL}"
echo ""

# Step 1: Send START event
echo -e "${YELLOW}Step 1: Sending START event...${NC}"

START_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/lineage" \
  -H 'Content-Type: application/json' \
  -d "{
        \"eventType\": \"START\",
        \"eventTime\": \"${TIMESTAMP}\",
        \"run\": {
          \"runId\": \"${RUN_ID}\"
        },
        \"job\": {
          \"namespace\": \"test-namespace\",
          \"name\": \"test-job\"
        },
        \"inputs\": [{
          \"namespace\": \"test-namespace\",
          \"name\": \"test-input-dataset\"
        }],  
        \"producer\": \"https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client\",
        \"schemaURL\": \"https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent\"
      }")

HTTP_CODE=$(echo "$START_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ START event sent successfully (HTTP ${HTTP_CODE})${NC}"
else
    echo -e "${RED}✗ Failed to send START event (HTTP ${HTTP_CODE})${NC}"
    echo "$START_RESPONSE"
    exit 1
fi

echo ""
sleep 2

# Step 2: Send COMPLETE event
echo -e "${YELLOW}Step 2: Sending COMPLETE event...${NC}"

COMPLETE_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

COMPLETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/lineage" \
  -H 'Content-Type: application/json' \
  -d "{
        \"eventType\": \"COMPLETE\",
        \"eventTime\": \"${COMPLETE_TIMESTAMP}\",
        \"run\": {
          \"runId\": \"${RUN_ID}\"
        },
        \"job\": {
          \"namespace\": \"test-namespace\",
          \"name\": \"test-job\"
        },
        \"outputs\": [{
          \"namespace\": \"test-namespace\",
          \"name\": \"test-output-dataset\",
          \"facets\": {
            \"schema\": {
              \"_producer\": \"https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client\",
              \"_schemaURL\": \"https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/spec/OpenLineage.json#/definitions/SchemaDatasetFacet\",
              \"fields\": [
                { \"name\": \"id\", \"type\": \"INTEGER\"},
                { \"name\": \"name\", \"type\": \"VARCHAR\"},
                { \"name\": \"created_at\", \"type\": \"TIMESTAMP\"}
              ]
            }
          }
        }],     
        \"producer\": \"https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client\",
        \"schemaURL\": \"https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent\"
      }")

HTTP_CODE=$(echo "$COMPLETE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ COMPLETE event sent successfully (HTTP ${HTTP_CODE})${NC}"
else
    echo -e "${RED}✗ Failed to send COMPLETE event (HTTP ${HTTP_CODE})${NC}"
    echo "$COMPLETE_RESPONSE"
    exit 1
fi

echo ""
sleep 2

# Step 3: Verify the data
echo -e "${YELLOW}Step 3: Verifying data was recorded...${NC}"

JOB_RESPONSE=$(curl -s "${API_URL}/api/v1/namespaces/test-namespace/jobs/test-job")

if echo "$JOB_RESPONSE" | grep -q "test-job"; then
    echo -e "${GREEN}✓ Job data verified${NC}"
else
    echo -e "${RED}✗ Could not verify job data${NC}"
    exit 1
fi

echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Test Completed Successfully!      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}View your lineage data:${NC}"
echo "  Web UI: ${WEB_URL}"
echo "  Search for: test-job"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo "  Job: ${API_URL}/api/v1/namespaces/test-namespace/jobs/test-job"
echo "  Run: ${API_URL}/api/v1/namespaces/test-namespace/jobs/test-job/runs/${RUN_ID}"
echo ""
echo -e "${BLUE}Datasets Created:${NC}"
echo "  Input:  test-input-dataset"
echo "  Output: test-output-dataset (with schema: id, name, created_at)"
echo ""
echo -e "${YELLOW}Tip: Open ${WEB_URL} and search for 'test-job' to see the lineage graph!${NC}"

# Made with Bob
