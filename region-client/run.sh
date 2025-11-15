#!/bin/bash
# Quick start script for region client

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Uptime Monitor Region Client Setup${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required variables
if [ -z "$API_BASE_URL" ] || [ -z "$REGION_CODE" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: Required environment variables not set${NC}"
    echo "Please set in .env file:"
    echo "  - API_BASE_URL"
    echo "  - REGION_CODE"
    echo "  - API_KEY"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run the client
echo -e "${GREEN}Starting region client...${NC}"
echo "Region: $REGION_CODE"
echo "API: $API_BASE_URL"
echo ""
python region_client.py
