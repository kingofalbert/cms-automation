#!/bin/bash

# Phase 7 E2E Test Runner
# Convenience script for running Phase 7 unified optimization tests

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
MODE=${1:-"local"}
SUITE=${2:-"all"}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 7 E2E Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Set test environment based on mode
if [ "$MODE" = "local" ]; then
    echo -e "${GREEN}Testing Environment:${NC} Local Development"
    echo -e "${GREEN}Frontend:${NC} http://localhost:4173"
    echo -e "${GREEN}Backend:${NC} http://localhost:8000"
    export TEST_LOCAL=1
elif [ "$MODE" = "prod" ]; then
    echo -e "${GREEN}Testing Environment:${NC} Production"
    echo -e "${GREEN}Frontend:${NC} https://storage.googleapis.com/cms-automation-frontend-2025/"
    echo -e "${GREEN}Backend:${NC} https://cms-automation-backend-baau2zqeqq-ue.a.run.app"
    export TEST_LOCAL=0
else
    echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
    echo "Usage: ./run-phase7-tests.sh [local|prod] [all|generation|quality|monitoring|errors|performance]"
    exit 1
fi

echo ""

# Check if services are running (local mode only)
if [ "$MODE" = "local" ]; then
    echo -e "${YELLOW}Checking services...${NC}"

    # Check backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is running"
    else
        echo -e "${RED}✗${NC} Backend is not running!"
        echo "  Start with: cd backend && uvicorn src.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi

    # Check frontend (optional, tests use API directly)
    if curl -s http://localhost:4173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend is running"
    else
        echo -e "${YELLOW}⚠${NC} Frontend is not running (optional for API tests)"
        echo "  Start with: cd frontend && npm run preview"
    fi

    echo ""
fi

# Determine which tests to run
case "$SUITE" in
    "all")
        echo -e "${BLUE}Running:${NC} All Phase 7 tests (22 tests)"
        TEST_PATTERN="phase7-unified-optimization"
        ;;
    "generation")
        echo -e "${BLUE}Running:${NC} Optimization Generation tests (7 tests)"
        TEST_PATTERN="-g 'Phase 7 - Unified Optimization Generation'"
        ;;
    "quality")
        echo -e "${BLUE}Running:${NC} Content Quality tests (5 tests)"
        TEST_PATTERN="-g 'Phase 7 - SEO and FAQ Content Quality'"
        ;;
    "monitoring")
        echo -e "${BLUE}Running:${NC} Monitoring & Cost Tracking tests (5 tests)"
        TEST_PATTERN="-g 'Phase 7 - Monitoring and Cost Tracking'"
        ;;
    "errors")
        echo -e "${BLUE}Running:${NC} Error Handling tests (3 tests)"
        TEST_PATTERN="-g 'Phase 7 - Error Handling'"
        ;;
    "performance")
        echo -e "${BLUE}Running:${NC} Performance Benchmark tests (2 tests)"
        TEST_PATTERN="-g 'Phase 7 - Performance Benchmarks'"
        ;;
    *)
        echo -e "${RED}Error: Invalid suite '$SUITE'${NC}"
        echo "Valid suites: all, generation, quality, monitoring, errors, performance"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Starting tests...${NC}"
echo ""

# Run tests
if eval "npx playwright test $TEST_PATTERN"; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "View detailed report: npx playwright show-report"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "View detailed report: npx playwright show-report"
    exit 1
fi
