# Makefile for CSC-Reach Multi-Channel Messaging System

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
	@echo "  build        - Build application for current platform"
	@echo "  build-macos  - Build macOS application"
	@echo "  build-windows - Build Windows application"
	@echo "  dmg          - Create macOS DMG installer"
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
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

# Platform-specific builds
build-macos:
	python scripts/build/build_macos.py

build-windows:
	python scripts/build/build_windows.py

dmg:
	python scripts/build/create_dmg.py

# Run targets
run:
	python src/multichannel_messaging/main.py

# Development setup
setup-dev: install-dev
	python scripts/dev/setup_dev.py

# Documentation
docs:
	@echo "📚 Documentation structure:"
	@echo "  docs/user/     - User guides and manuals"
	@echo "  docs/dev/      - Developer documentation"
	@echo "  docs/api/      - API documentation"
	@echo "  docs/summaries/ - Implementation summaries"

# Project structure
structure:
	@echo "📁 Project structure:"
	@tree -I 'venv|__pycache__|*.egg-info|build' -L 3
