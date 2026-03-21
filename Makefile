.PHONY: help install install-dev setup lint format test serve clean check-uv

# Default target
help:
	@echo "NLCRUD Project - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install         - Install dependencies with uv"
	@echo "  make install-dev     - Install dev dependencies with uv"
	@echo "  make setup           - Full setup (install + hooks + lock file)"
	@echo ""
	@echo "Development:"
	@echo "  make lint            - Run code linters (black, isort, mypy)"
	@echo "  make format          - Format code with black and isort"
	@echo "  make test            - Run test suite"
	@echo ""
	@echo "Running:"
	@echo "  make serve           - Start the API server"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           - Remove cache and temp files"
	@echo "  make check-uv        - Verify uv is installed and configured"
	@echo ""
	@echo "Note: All commands use 'uv' for package management."
	@echo "      Never use pip, pip3, poetry, or setuptools directly."
	@echo ""

# Check if uv is installed
check-uv:
	@command -v uv >/dev/null 2>&1 || { echo "ERROR: uv is not installed!"; echo "Install from: https://github.com/astral-sh/uv"; exit 1; }
	@echo "✓ uv is installed: $$(uv --version)"

# Install dependencies
install: check-uv
	@echo "Installing dependencies with uv..."
	uv pip install -e .

# Install dev dependencies
install-dev: check-uv
	@echo "Installing dev dependencies with uv..."
	uv pip install -e ".[dev,test]"

# Setup pre-commit hooks
setup-hooks:
	@command -v pre-commit >/dev/null 2>&1 || { echo "Installing pre-commit..."; uv pip install pre-commit; }
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Create lock file
lock: check-uv
	@echo "Creating uv.lock file..."
	uv pip compile pyproject.toml -o uv.lock
	@echo "✓ Lock file created"

# Full setup
setup: check-uv install-dev setup-hooks lock
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Verify spaCy model: python -m spacy download en_core_web_sm"
	@echo "  2. Initialize database: python -m nlcrud.db.init"
	@echo "  3. Start server: make serve"

# Code formatting
format: check-uv
	@echo "Formatting code..."
	uv run black nlcrud tests
	uv run isort nlcrud tests
	@echo "✓ Code formatted"

# Code linting
lint: check-uv
	@echo "Linting code..."
	uv run black --check nlcrud tests
	uv run isort --check-only nlcrud tests
	@echo "✓ Linting passed"

# Run tests
test: check-uv
	@echo "Running tests..."
	uv run pytest tests/ -v --tb=short
	@echo "✓ Tests completed"

# Start the server
serve: check-uv
	@echo "Starting server..."
	uv run python main.py serve

# Clean cache
clean:
	@echo "Cleaning cache and temp files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# Deprecated warnings
.PHONY: pip pip-install poetry pip-install-r
pip pip-install poetry pip-install-r:
	@echo "ERROR: '$(MAKECMDGOALS)' is not allowed!"
	@echo "Use 'uv' instead. Example:"
	@echo "  uv pip install <package>"
	@echo "  uv pip install -e ."
	@echo ""
	@echo "For help, run: make help"
	@exit 1
