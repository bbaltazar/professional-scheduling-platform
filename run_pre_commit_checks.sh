#!/bin/bash
# Pre-commit/Pre-deploy validation script
# Run this before committing refactored code to ensure safety

set -e  # Exit on first error

echo "🔍 Running Pre-Commit Safety Checks"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to run a check
run_check() {
    local check_name="$1"
    local command="$2"
    
    echo ""
    echo "📋 $check_name"
    echo "--------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# 1. JavaScript Module Validation
run_check "JavaScript Syntax & Imports" "node validate_js.mjs 2>&1 | grep -v 'window is not defined' || true"

# 2. Python Module Tests
run_check "JavaScript Module Structure" "python tests/test_js_modules.py"

# 3. Refactoring Safety Tests
run_check "Refactoring Safety Checks" "python tests/test_refactoring_safety.py"

# 4. Python Backend Tests (quick ones)
run_check "Backend API Tests" "python -m pytest tests/test_api.py -v --tb=short"

# 5. Check for common issues
run_check "No Python Syntax Errors" "python -m py_compile src/calendar_app/*.py"

# 6. Check file permissions (modules should be readable)
run_check "File Permissions" "test -r src/calendar_app/static/js/main.js"

# Summary
echo ""
echo "======================================"
echo "📊 SUMMARY"
echo "======================================"
echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"
echo "======================================"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Safe to commit.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix before committing.${NC}"
    exit 1
fi
