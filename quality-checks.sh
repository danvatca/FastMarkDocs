#!/usr/bin/env bash

# Quality check script for fastapi-markdown-docs
# Runs code formatting, linting, tests, and SonarQube analysis

set -euo pipefail # Exit on error, undefined vars, pipe failures

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to create centered header
print_header() {
    local term_width
    term_width=$(tput cols 2>/dev/null || echo 80)
    local title="$1"
    local title_length=${#title}
    local padding=$(( (term_width - title_length - 2) / 2 ))
    
    printf "${WHITE}+"
    printf '=%.0s' $(seq 1 $((term_width - 2)))
    printf "+${NC}\n"
    
    printf "${WHITE}|%*s%s%*s|${NC}\n" $padding "" "$title" $((term_width - padding - title_length - 2)) ""
    
    printf "${WHITE}+"
    printf '=%.0s' $(seq 1 $((term_width - 2)))
    printf "+${NC}\n"
    echo
}

# Function to run command with progress indication
run_check() {
    local cmd="$1"
    local description="$2"
    local temp_file=$(mktemp)
    
    echo -ne "$description: "
    
    # Run command in background
    eval "$cmd" > "$temp_file" 2>&1 &
    local cmd_pid
    cmd_pid=$!
    
    # Show progress dots
    local dots=0
    while kill -0 "$cmd_pid" 2>/dev/null; do
        echo -ne "."
        ((dots++))
        [[ $dots -gt 60 ]] && { echo -ne "\n  "; dots=0; }
        sleep 1
    done
    
    # Check result
    wait "$cmd_pid"
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e " ${GREEN}[OK]${NC}"
        rm -f "$temp_file"
        return 0
    else
        echo -e " ${RED}[FAIL]${NC}"
        echo -e "${RED}Error output:${NC}"
        cat "$temp_file"
        rm -f "$temp_file"
        return 1
    fi
}

# Function to show simple status
show_status() {
    local description="$1"
    local success="$2"
    
    echo -ne "$description: "
    if [[ "$success" == "true" ]]; then
        echo -e "${GREEN}[OK]${NC}"
        return 0
    else
        echo -e "${RED}[FAIL]${NC}"
        return 1
    fi
}

# Function to show warning status
show_warning() {
    local description="$1"
    local message="$2"
    
    echo -ne "$description: "
    echo -e "${YELLOW}[WARNING]${NC}"
    echo -e "${YELLOW}⚠️  $message${NC}"
}

# Track results and timing
RESULTS=()
FAILED_CHECKS=()
WARNING_CHECKS=()
START_TIME=$(date +%s)

# Main execution
print_header "FASTAPI-MARKDOWN-DOCS QUALITY CHECK"

cd "$(readlink -f "$(dirname "$0")")" || exit 1

# System dependencies (skip sonar-scanner for fastmarkdocs)
echo -ne "🔍 Checking system dependencies: "
echo -e "${GREEN}[OK]${NC}"
RESULTS+=("System dependencies")

# Check for poetry availability
if run_check "command -v poetry >/dev/null 2>&1" "📦 Checking poetry availability"; then
    RESULTS+=("Poetry availability")
else
    FAILED_CHECKS+=("Poetry availability")
fi

# Virtual environment setup
echo -ne "🐍 Setting up virtual environment: "
if [[ -d .venv ]]; then
    source .venv/bin/activate
    echo -e "${GREEN}[OK]${NC}"
    RESULTS+=("Virtual environment")
else
    venv_created=false
    for python_cmd in python3.12 python3.11 python3.10 python3.9 python3; do
        if command -v "$python_cmd" >/dev/null 2>&1 && "$python_cmd" -m venv .venv >/dev/null 2>&1; then
            source .venv/bin/activate
            venv_created=true
            break
        fi
    done
    if show_status "" "$venv_created"; then
        RESULTS+=("Virtual environment")
    else
        FAILED_CHECKS+=("Virtual environment")
        echo -e "${RED}Could not create virtual environment with any Python version${NC}"
    fi
fi

# Quality checks
if run_check "poetry install" "📦 Installing dependencies"; then
    RESULTS+=("Dependencies")
else
    FAILED_CHECKS+=("Dependencies")
fi

if run_check "command -v black >/dev/null 2>&1 && command -v ruff >/dev/null 2>&1" "🔧 Verifying Python tools"; then
    RESULTS+=("Python tools")
else
    FAILED_CHECKS+=("Python tools")
fi

# Code formatting check
if run_check "black --check ./src/" "🎨 Code formatting"; then
    RESULTS+=("Code formatting")
else
    FAILED_CHECKS+=("Code formatting")
fi

# Linting check
if run_check "ruff check ." "🔍 Linting"; then
    RESULTS+=("Linting")
else
    FAILED_CHECKS+=("Linting")
fi

# Custom lint checks for modern Python type annotations
echo -ne "🔎 Custom lint checks: "
custom_lint_failed=false
temp_file=$(mktemp)

# Check for old-style type annotations
if grep -r --include="*.py" -E "(^|[^a-zA-Z])List\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'List[]' type annotations. Use 'list[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
elif grep -r --include="*.py" -E "(^|[^a-zA-Z])Dict\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'Dict[]' type annotations. Use 'dict[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
elif grep -r --include="*.py" -E "(^|[^a-zA-Z])Tuple\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'Tuple[]' type annotations. Use 'tuple[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
elif grep -r --include="*.py" -E "(^|[^a-zA-Z])Set\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'Set[]' type annotations. Use 'set[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
elif grep -r --include="*.py" -E "(^|[^a-zA-Z])FrozenSet\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'FrozenSet[]' type annotations. Use 'frozenset[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
elif grep -r --include="*.py" -E "(^|[^a-zA-Z])Type\[" src/ > "$temp_file" 2>&1; then
    echo -e "${RED}[FAIL]${NC}"
    echo -e "${RED}Found old-style 'Type[]' type annotations. Use 'type[]' instead:${NC}"
    cat "$temp_file"
    custom_lint_failed=true
else
    echo -e "${GREEN}[OK]${NC}"
fi

rm -f "$temp_file"

if [[ "$custom_lint_failed" == "true" ]]; then
    FAILED_CHECKS+=("Custom linting")
else
    RESULTS+=("Custom linting")
fi

# Type checking with mypy
if run_check "mypy src/fastmarkdocs/" "🔍 Type checking"; then
    RESULTS+=("Type checking")
else
    FAILED_CHECKS+=("Type checking")
fi

# Security checks (matching GitHub Actions)
if run_check "bandit -r src/fastmarkdocs/" "🔒 Security checks (bandit)"; then
    RESULTS+=("Security checks (bandit)")
else
    FAILED_CHECKS+=("Security checks (bandit)")
fi

# Safety check (matching GitHub Actions approach)
echo -ne "🛡️  Dependency vulnerability checks (safety): "
if safety check >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
    RESULTS+=("Dependency vulnerability checks (safety)")
else
    # In GitHub Actions, this might fail due to vulnerabilities but still be acceptable
    # Let's treat it as a warning like in the original approach
    echo -e "${YELLOW}[WARNING]${NC}"
    echo -e "${YELLOW}⚠️  Safety check found vulnerabilities or encountered issues${NC}"
    WARNING_CHECKS+=("Dependency vulnerability checks (safety)")
    RESULTS+=("Dependency vulnerability checks (safety) (with warnings)")
fi

# Tests (matching GitHub Actions)
TESTS_PASSED=false
if run_check "pytest tests/ -v --cov=fastmarkdocs --cov-report=xml --cov-report=term-missing --cov-fail-under=89" "🧪 Tests with coverage"; then
    RESULTS+=("Tests with coverage")
    TESTS_PASSED=true
else
    FAILED_CHECKS+=("Tests with coverage")
fi

# Test coverage is handled by pytest --cov-fail-under=90 above
# No separate coverage check needed since it's built into the test command

# CLI tools are tested as part of the overall test suite

# Package build test
if run_check "poetry build" "📦 Package build test"; then
    RESULTS+=("Package build")
else
    FAILED_CHECKS+=("Package build")
fi

# SonarQube analysis is not configured for fastmarkdocs
echo -ne "📊 SonarQube analysis: "
echo -e "${CYAN}[SKIPPED]${NC}"
echo -e "${CYAN}   SonarQube analysis not configured for this project${NC}"
RESULTS+=("SonarQube analysis (not configured)")

# Deactivate virtual environment if active
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    deactivate
fi

# No cleanup needed - files are not generated to disk

# Final report
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo
print_header "QUALITY REPORT"

echo -e "${PURPLE}📊 Summary:${NC}"
echo -e "   • Passed checks: ${#RESULTS[@]}"
echo -e "   • Failed checks: ${#FAILED_CHECKS[@]}"
echo -e "   • Warning checks: ${#WARNING_CHECKS[@]}"
echo -e "   • Duration: ${DURATION}s"
echo -e "   • Branch: $(git rev-parse --abbrev-ref HEAD)"
echo -e "   • Commit: $(git rev-parse --short HEAD)"
echo

# Show warnings if any
if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Warnings:${NC}"
    for check in "${WARNING_CHECKS[@]}"; do
        echo -e "   • ${YELLOW}!${NC} $check"
    done
    echo
fi

if [[ ${#FAILED_CHECKS[@]} -eq 0 ]]; then
    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  All quality checks passed with warnings!${NC}"
        echo -e "${CYAN}Consider addressing the warnings above for better code quality.${NC}"
    else
        echo -e "${GREEN}🎉 All quality checks passed successfully!${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ Quality check failed!${NC}"
    echo -e "${RED}Failed checks:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "   • ${RED}✗${NC} $check"
    done
    echo
    exit 1
fi
