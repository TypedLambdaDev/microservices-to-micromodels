#!/bin/bash
# Enforce uv for package management
# This script checks for non-uv package management files and warns about them

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Checking uv enforcement..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv is not installed${NC}"
    echo "  Install from: https://github.com/astral-sh/uv"
    exit 1
fi

echo -e "${GREEN}✓ uv is installed: $(uv --version)${NC}"
echo ""

# Check for forbidden files
FORBIDDEN_FILES=(
    "poetry.lock"
    "Poetry.lock"
    "pdm.lock"
    "setup.cfg"
)

FOUND_FORBIDDEN=0
for file in "${FORBIDDEN_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo -e "${RED}✗ Found forbidden file: $file${NC}"
        echo "  This file indicates use of non-uv package management"
        FOUND_FORBIDDEN=1
    fi
done

if [ $FOUND_FORBIDDEN -eq 1 ]; then
    echo ""
    echo "To migrate:"
    echo "  1. Remove old package manager files"
    echo "  2. Use: uv pip install"
    echo ""
fi

# Check for pip in recent commits
echo "Checking git history for pip usage..."
if git log --all --oneline --grep="pip install" 2>/dev/null | head -3; then
    echo -e "${YELLOW}⚠ Found commits mentioning pip${NC}"
    echo "  Consider using uv instead in future commits"
    echo ""
fi

# Check for pip in tracked files (excluding this script)
echo "Checking for pip references in code..."
if grep -r "pip install" . --include="*.py" --include="*.sh" --include="Dockerfile*" --include="*.md" 2>/dev/null | grep -v "scripts/enforce_uv.sh" | grep -v "enforce_uv" | head -3; then
    echo -e "${YELLOW}⚠ Found pip references in code/docs${NC}"
    echo "  Update to recommend uv instead"
    echo ""
fi

# Check pyproject.toml exists
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo -e "${RED}✗ Missing pyproject.toml${NC}"
    echo "  Create one with modern Python packaging format"
    exit 1
fi

echo -e "${GREEN}✓ pyproject.toml exists${NC}"
echo ""

# Check lock file
if [ ! -f "$PROJECT_ROOT/uv.lock" ]; then
    echo -e "${YELLOW}⚠ No uv.lock file found${NC}"
    echo "  Generate with: uv pip compile pyproject.toml -o uv.lock"
else
    echo -e "${GREEN}✓ uv.lock file exists${NC}"
fi

echo ""
echo -e "${GREEN}Enforcement check passed!${NC}"
echo ""
echo "Usage:"
echo "  uv pip install <package>          # Install package"
echo "  uv pip install -e .[dev]          # Install with dev dependencies"
echo "  uv pip compile pyproject.toml     # Generate lock file"
echo "  uv run <command>                  # Run Python scripts"
echo ""
