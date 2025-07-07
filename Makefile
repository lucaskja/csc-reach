# Makefile for Multi-Channel Bulk Messaging System

.PHONY: help install install-dev test test-unit test-integration lint format clean build run

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build application"
	@echo "  run          - Run the application"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing targets
test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-coverage:
	pytest --cov=src/multichannel_messaging --cov-report=html --cov-report=term

# Code quality targets
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

type-check:
	mypy src/

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

# Run targets
run:
	python src/multichannel_messaging/main.py

# Development setup
setup-dev: install-dev
	pre-commit install

# Package building
build-windows:
	pyinstaller scripts/build_windows.spec

build-macos:
	pyinstaller scripts/build_macos.spec
