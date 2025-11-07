#!/bin/bash
# Pre-deployment check script for Google Docs HTML parsing feature
# Usage: ./scripts/pre-deployment-check.sh

set -e  # Exit on error

echo "======================================================================="
echo "Google Docs HTML Parsing - Pre-Deployment Checks"
echo "======================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Git Status"
echo "-------------------------------------------------------------------"

# Check if on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" = "main" ]; then
    check_pass "On main branch"
else
    check_warn "Not on main branch (current: $CURRENT_BRANCH)"
fi

# Check if latest commit is the HTML parsing fix
LATEST_COMMIT=$(git log --oneline -1)
if echo "$LATEST_COMMIT" | grep -q "google-drive.*HTML"; then
    check_pass "Latest commit is Google Docs HTML parsing fix"
else
    check_warn "Latest commit may not be the expected fix"
    echo "  Latest: $LATEST_COMMIT"
fi

# Check if pushed to remote
if git diff origin/main..HEAD --quiet 2>/dev/null; then
    check_pass "All commits pushed to remote"
else
    check_fail "Unpushed commits detected"
fi

echo ""
echo "2. Checking File Existence"
echo "-------------------------------------------------------------------"

# Check if all new files exist
FILES_TO_CHECK=(
    "backend/src/services/google_drive/metrics.py"
    "backend/src/services/google_drive/sync_service.py"
    "backend/tests/services/test_google_docs_html_parser.py"
    "backend/tests/integration/test_google_doc_html_parsing.py"
    "test_html_parser_standalone.py"
    "GOOGLE_DOC_PARSING_FIX.md"
    "DEPLOYMENT_CHECKLIST.md"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File exists: $file"
    else
        check_fail "File missing: $file"
    fi
done

echo ""
echo "3. Running Tests"
echo "-------------------------------------------------------------------"

# Run standalone integration tests
if python3 test_html_parser_standalone.py > /tmp/test_output.log 2>&1; then
    PASSED=$(grep "passed" /tmp/test_output.log | tail -1 | awk '{print $2}')
    FAILED=$(grep "failed" /tmp/test_output.log | tail -1 | awk '{print $4}')
    
    if [ "$FAILED" = "0" ]; then
        check_pass "All integration tests passed ($PASSED/$(($PASSED + $FAILED)))"
    else
        check_fail "Some tests failed ($FAILED failures)"
    fi
else
    check_fail "Test execution failed"
fi

echo ""
echo "4. Code Quality Checks"
echo "-------------------------------------------------------------------"

# Check Python syntax
if python3 -m py_compile backend/src/services/google_drive/sync_service.py 2>/dev/null; then
    check_pass "sync_service.py: Python syntax valid"
else
    check_fail "sync_service.py: Syntax errors detected"
fi

if python3 -m py_compile backend/src/services/google_drive/metrics.py 2>/dev/null; then
    check_pass "metrics.py: Python syntax valid"
else
    check_fail "metrics.py: Syntax errors detected"
fi

# Check for common issues
if grep -q "text/html" backend/src/services/google_drive/sync_service.py; then
    check_pass "Using text/html export (not text/plain)"
else
    check_fail "Not using text/html export"
fi

if grep -q "GoogleDocsHTMLParser" backend/src/services/google_drive/sync_service.py; then
    check_pass "GoogleDocsHTMLParser class found"
else
    check_fail "GoogleDocsHTMLParser class not found"
fi

if grep -q "GoogleDriveMetricsCollector" backend/src/services/google_drive/metrics.py; then
    check_pass "Metrics collector implemented"
else
    check_fail "Metrics collector not found"
fi

echo ""
echo "5. Documentation Checks"
echo "-------------------------------------------------------------------"

# Check documentation exists and has content
if [ -f "GOOGLE_DOC_PARSING_FIX.md" ]; then
    LINES=$(wc -l < GOOGLE_DOC_PARSING_FIX.md)
    if [ "$LINES" -gt 100 ]; then
        check_pass "GOOGLE_DOC_PARSING_FIX.md exists ($LINES lines)"
    else
        check_warn "GOOGLE_DOC_PARSING_FIX.md may be incomplete ($LINES lines)"
    fi
fi

if [ -f "DEPLOYMENT_CHECKLIST.md" ]; then
    check_pass "DEPLOYMENT_CHECKLIST.md exists"
fi

echo ""
echo "======================================================================="
echo "Pre-Deployment Check Summary"
echo "======================================================================="
echo ""
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed. Ready for deployment!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix issues before deploying.${NC}"
    exit 1
fi
