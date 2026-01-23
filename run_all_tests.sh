#!/bin/bash

# One-click script to run all nlp2cmd tests
# This script will:
# 1. Generate schemas for all commands
# 2. Run the enhanced test script
# 3. Show results summary

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== NLP2CMD Complete Test Runner ===${NC}"
echo ""

# Step 1: Generate schemas using app2schema
echo -e "${YELLOW}Step 1: Generating command schemas using app2schema...${NC}"
if command -v python &> /dev/null; then
    # Generate schema for docker
    python -m app2schema docker --type shell -o generated_schemas/docker.appspec.json 2>/dev/null || echo "Docker schema generation skipped"
    # Generate schema for nginx
    python -m app2schema nginx --type shell -o generated_schemas/nginx.appspec.json 2>/dev/null || echo "Nginx schema generation skipped"
    echo -e "${GREEN}✓ Schemas generated using app2schema${NC}"
else
    echo -e "${YELLOW}! Python not found, skipping schema generation${NC}"
fi
echo ""

# Step 2: Run tests
echo -e "${YELLOW}Step 2: Running nlp2cmd tests...${NC}"
if [ -f "./test_nlp2cmd_enhanced.sh" ]; then
    ./test_nlp2cmd_enhanced.sh
else
    echo -e "${YELLOW}! test_nlp2cmd_enhanced.sh not found, falling back to basic test${NC}"
    if [ -f "./test_nlp2cmd_commands.sh" ]; then
        ./test_nlp2cmd_commands.sh
    else
        echo "Error: No test script found!"
        exit 1
    fi
fi
echo ""

# Step 3: Show summary
echo -e "${YELLOW}Step 3: Test Summary${NC}"
if [ -f "./nlp2cmd_test.log" ]; then
    echo "Full log available at: ./nlp2cmd_test.log"
    echo ""
    echo "Last 10 lines of log:"
    echo "---------------------"
    tail -n 10 ./nlp2cmd_test.log
fi

echo ""
echo -e "${GREEN}=== Test Complete! ===${NC}"
