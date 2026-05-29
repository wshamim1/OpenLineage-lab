#!/bin/bash

# OpenLineage/Marquez Podman Shutdown Script
# This script stops and removes Marquez containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping OpenLineage/Marquez services...${NC}"
echo ""

# Check if podman-compose is available
if command -v podman-compose &> /dev/null; then
    echo "Using podman-compose..."
    podman-compose down
else
    echo "Using podman commands..."
    
    # Stop and remove containers
    for container in marquez-web marquez-api marquez-db; do
        if podman ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            echo "Stopping and removing $container..."
            podman stop $container 2>/dev/null || true
            podman rm $container 2>/dev/null || true
        fi
    done
fi

echo ""
echo -e "${GREEN}✓ Services stopped.${NC}"
echo ""
echo "To remove volumes (this will delete all data):"
echo "  podman volume rm marquez-db-data"
echo ""
echo "To remove network:"
echo "  podman network rm marquez-network"

# Made with Bob
