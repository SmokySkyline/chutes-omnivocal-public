.PHONY: help install install-dev test test-cov lint format clean doctor

help:
	@echo "Omnivocal - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install package with uv"
	@echo "  make install-dev     Install package with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-cov        Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run type checking with mypy"
	@echo "  make format          Format code with black"
	@echo "  make format-check    Check code formatting"
	@echo ""
	@echo "Utilities:"
	@echo "  make doctor          Run system diagnostics"
	@echo "  make clean           Remove temporary files"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	uv run pytest -v

test-cov:
	uv run pytest -v --cov=src/omnivocal --cov-report=term-missing --cov-report=html

lint:
	uv run mypy src/omnivocal

format:
	uv run black src/ tests/

format-check:
	uv run black --check src/ tests/

doctor:
	uv run ovstt doctor

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleaned temporary files"
