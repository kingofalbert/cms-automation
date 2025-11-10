#!/bin/bash

###############################################################################
# CMS Automation E2E Regression Test Runner
#
# This script provides convenient ways to run regression tests with various
# configurations and options.
#
# Usage:
#   ./run-tests.sh [command] [options]
#
# Commands:
#   all          - Run all regression tests
#   worklist     - Run worklist tests only
#   proofreading - Run proofreading tests only
#   settings     - Run settings tests only
#   devtools     - Run Chrome DevTools integration tests
#   complete     - Run complete regression suite
#   smoke        - Run quick smoke tests
#   ci           - Run tests in CI mode
#
# Options:
#   --local      - Test against local development server
#   --headed     - Show browser window
#   --ui         - Use Playwright UI mode
#   --debug      - Run in debug mode
#   --workers N  - Number of parallel workers (default: 4)
#   --retries N  - Number of retries for failed tests (default: 0)
#
# Examples:
#   ./run-tests.sh all
#   ./run-tests.sh worklist --headed
#   ./run-tests.sh complete --local
#   ./run-tests.sh smoke --ui
#   ./run-tests.sh ci --workers=1 --retries=2
#
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COMMAND=""
TEST_FILE=""
EXTRA_ARGS=""
LOCAL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    all|worklist|proofreading|settings|devtools|complete|smoke|ci)
      COMMAND="$1"
      shift
      ;;
    --local)
      LOCAL=true
      shift
      ;;
    --headed)
      EXTRA_ARGS="$EXTRA_ARGS --headed"
      shift
      ;;
    --ui)
      EXTRA_ARGS="$EXTRA_ARGS --ui"
      shift
      ;;
    --debug)
      EXTRA_ARGS="$EXTRA_ARGS --debug"
      shift
      ;;
    --workers=*)
      EXTRA_ARGS="$EXTRA_ARGS $1"
      shift
      ;;
    --retries=*)
      EXTRA_ARGS="$EXTRA_ARGS $1"
      shift
      ;;
    *)
      echo -e "${RED}Unknown argument: $1${NC}"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CMS Automation E2E Regression Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate command
if [ -z "$COMMAND" ]; then
  echo -e "${RED}Error: No command specified${NC}"
  echo ""
  echo "Usage: ./run-tests.sh [command] [options]"
  echo ""
  echo "Available commands:"
  echo "  all          - Run all regression tests"
  echo "  worklist     - Run worklist tests only"
  echo "  proofreading - Run proofreading tests only"
  echo "  settings     - Run settings tests only"
  echo "  devtools     - Run Chrome DevTools integration tests"
  echo "  complete     - Run complete regression suite"
  echo "  smoke        - Run quick smoke tests"
  echo "  ci           - Run tests in CI mode"
  echo ""
  exit 1
fi

# Set test file based on command
case $COMMAND in
  all)
    TEST_FILE="e2e/regression/*.spec.ts"
    ;;
  worklist)
    TEST_FILE="e2e/regression/worklist.spec.ts"
    ;;
  proofreading)
    TEST_FILE="e2e/regression/proofreading-review.spec.ts"
    ;;
  settings)
    TEST_FILE="e2e/regression/settings.spec.ts"
    ;;
  devtools)
    TEST_FILE="e2e/regression/chrome-devtools-integration.spec.ts"
    ;;
  complete)
    TEST_FILE="e2e/regression/complete-regression.spec.ts"
    ;;
  smoke)
    # Smoke tests: just basic loading tests
    TEST_FILE="e2e/regression/*.spec.ts"
    EXTRA_ARGS="$EXTRA_ARGS -g \"load|Load\""
    ;;
  ci)
    TEST_FILE="e2e/regression/*.spec.ts"
    EXTRA_ARGS="$EXTRA_ARGS --workers=1 --retries=2 --reporter=html,line"
    ;;
esac

# Print configuration
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Command: ${YELLOW}$COMMAND${NC}"
echo -e "  Test Files: ${YELLOW}$TEST_FILE${NC}"
if [ "$LOCAL" = true ]; then
  echo -e "  Environment: ${YELLOW}Local Development${NC}"
  export TEST_LOCAL=1
else
  echo -e "  Environment: ${YELLOW}Production${NC}"
fi
if [ -n "$EXTRA_ARGS" ]; then
  echo -e "  Extra Args: ${YELLOW}$EXTRA_ARGS${NC}"
fi
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}Installing dependencies...${NC}"
  npm install
  echo ""
fi

# Check if Playwright browsers are installed
if [ ! -d "node_modules/playwright/.local-browsers" ]; then
  echo -e "${YELLOW}Installing Playwright browsers...${NC}"
  npx playwright install chromium
  echo ""
fi

# Create test-results directory if it doesn't exist
mkdir -p test-results/screenshots

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo ""

START_TIME=$(date +%s)

# Run the tests
if eval "npx playwright test $TEST_FILE $EXTRA_ARGS"; then
  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))

  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}✅ Tests passed!${NC}"
  echo -e "${GREEN}Duration: ${DURATION}s${NC}"
  echo -e "${GREEN}========================================${NC}"

  # Show report link
  if [ -d "playwright-report" ]; then
    echo ""
    echo -e "${BLUE}📊 View detailed report:${NC}"
    echo -e "   npx playwright show-report"
  fi

  # Show screenshots
  SCREENSHOT_COUNT=$(ls -1 test-results/screenshots/*.png 2>/dev/null | wc -l)
  if [ "$SCREENSHOT_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${BLUE}📸 Screenshots captured: $SCREENSHOT_COUNT${NC}"
    echo -e "   See: test-results/screenshots/"
  fi

  exit 0
else
  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))

  echo ""
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}❌ Tests failed!${NC}"
  echo -e "${RED}Duration: ${DURATION}s${NC}"
  echo -e "${RED}========================================${NC}"

  # Show report link
  if [ -d "playwright-report" ]; then
    echo ""
    echo -e "${YELLOW}📊 View failure report:${NC}"
    echo -e "   npx playwright show-report"
  fi

  # Show screenshots
  SCREENSHOT_COUNT=$(ls -1 test-results/screenshots/*.png 2>/dev/null | wc -l)
  if [ "$SCREENSHOT_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}📸 Screenshots captured: $SCREENSHOT_COUNT${NC}"
    echo -e "   See: test-results/screenshots/"
  fi

  # Show traces
  if [ -d "test-results" ]; then
    TRACE_COUNT=$(find test-results -name "*trace.zip" 2>/dev/null | wc -l)
    if [ "$TRACE_COUNT" -gt 0 ]; then
      echo ""
      echo -e "${YELLOW}🔍 Traces available:${NC}"
      find test-results -name "*trace.zip" -exec echo "   {}" \;
      echo -e "   View with: npx playwright show-trace <trace-file>"
    fi
  fi

  exit 1
fi
