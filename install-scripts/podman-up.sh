#!/bin/bash

# OpenLineage/Marquez Podman Startup Script
# This script starts Marquez with Podman instead of Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
API_PORT=5000
TAG="latest"
BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --api-port)
      API_PORT="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --build)
      BUILD=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --api-port PORT    Set API port (default: 5000)"
      echo "  --tag VERSION      Use specific image tag (default: latest)"
      echo "  --build            Build images from source (requires Marquez repo)"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}Starting OpenLineage/Marquez with Podman...${NC}"
echo ""

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed.${NC}"
    echo "Please install Podman first:"
    echo "  macOS: brew install podman"
    echo "  Linux: See https://podman.io/getting-started/installation"
    exit 1
fi

# Check if podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: podman-compose is not installed.${NC}"
    echo "Installing podman-compose is recommended for easier management."
    echo "Install with: pip3 install podman-compose"
    echo ""
    echo -e "${YELLOW}Falling back to podman commands...${NC}"
    USE_COMPOSE=false
else
    USE_COMPOSE=true
fi

# Initialize podman machine if on macOS and not running
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! podman machine list | grep -q "Currently running"; then
        echo -e "${YELLOW}Podman machine not running. Starting...${NC}"
        if ! podman machine list | grep -q "podman-machine-default"; then
            echo "Initializing podman machine..."
            podman machine init
        fi
        podman machine start
        echo -e "${GREEN}Podman machine started.${NC}"
    fi
fi

# Update API port in docker-compose.yml if different from default
if [ "$API_PORT" != "5000" ]; then
    echo -e "${YELLOW}Configuring API to use port $API_PORT...${NC}"
    sed -i.bak "s/\"5000:5000\"/\"$API_PORT:5000\"/" docker-compose.yml
fi

# Update image tags if specified
if [ "$TAG" != "latest" ]; then
    echo -e "${YELLOW}Using image tag: $TAG${NC}"
    sed -i.bak "s/:latest/:$TAG/g" docker-compose.yml
fi

# Start services
if [ "$USE_COMPOSE" = true ]; then
    echo -e "${GREEN}Starting services with podman-compose...${NC}"
    podman-compose up -d
else
    echo -e "${GREEN}Starting services with podman...${NC}"
    
    # Create network
    podman network exists marquez-network || podman network create marquez-network
    
    # Create volume
    podman volume exists marquez-db-data || podman volume create marquez-db-data
    
    # Start PostgreSQL
    echo "Starting PostgreSQL..."
    podman run -d \
        --name marquez-db \
        --network marquez-network \
        -p 5432:5432 \
        -e POSTGRES_USER=marquez \
        -e POSTGRES_PASSWORD=marquez \
        -e POSTGRES_DB=marquez \
        -v marquez-db-data:/var/lib/postgresql/data \
        docker.io/library/postgres:15
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Start Marquez API
    echo "Starting Marquez API..."
    podman run -d \
        --name marquez-api \
        --network marquez-network \
        -p $API_PORT:5000 \
        -p 5001:5001 \
        -e MARQUEZ_PORT=5000 \
        -e MARQUEZ_ADMIN_PORT=5001 \
        -e POSTGRES_HOST=marquez-db \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_DB=marquez \
        -e POSTGRES_USER=marquez \
        -e POSTGRES_PASSWORD=marquez \
        docker.io/marquezproject/marquez:$TAG
    
    # Wait for API to be ready
    echo "Waiting for Marquez API to be ready..."
    sleep 15
    
    # Start Marquez Web UI
    echo "Starting Marquez Web UI..."
    podman run -d \
        --name marquez-web \
        --network marquez-network \
        -p 3000:3000 \
        -e MARQUEZ_HOST=marquez-api \
        -e MARQUEZ_PORT=5000 \
        docker.io/marquezproject/marquez-web:$TAG
fi

echo ""
echo -e "${GREEN}✓ OpenLineage/Marquez is starting up!${NC}"
echo ""
echo "Services:"
echo "  - Marquez UI:  http://localhost:3000"
echo "  - Marquez API: http://localhost:$API_PORT"
echo "  - PostgreSQL:  localhost:5432"
echo ""
echo "To view logs:"
if [ "$USE_COMPOSE" = true ]; then
    echo "  podman-compose logs -f"
else
    echo "  podman logs -f marquez-api"
    echo "  podman logs -f marquez-web"
    echo "  podman logs -f marquez-db"
fi
echo ""
echo "To stop services:"
if [ "$USE_COMPOSE" = true ]; then
    echo "  podman-compose down"
else
    echo "  ./podman-down.sh"
fi
echo ""
echo -e "${YELLOW}Note: It may take a minute for all services to be fully ready.${NC}"

