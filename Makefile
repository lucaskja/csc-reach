# Makefile for CSC-Reach Multi-Channel Messaging System

.PHONY: help install install-dev test test-unit test-integration lint format clean build run

# Default target
help:
	@echo "CSC-Reach Build System"
	@echo "======================"
	@echo ""
	@echo "🏗️  Build Commands:"
	@echo "  build            - Build for all platforms (enhanced)"
	@echo "  build-quick      - Quick build with simple interface"
	@echo "  build-macos      - Build macOS application only"
	@echo "  build-windows    - Build Windows application only"
	@echo "  build-clean      - Clean build and rebuild all"
	@echo "  dmg              - Create macOS DMG installer"
	@echo "  zip-windows      - Create Windows ZIP distribution"
	@echo ""
	@echo "📦 Quick Build Commands:"
	@echo "  make quick               # Build everything (simple)"
	@echo "  make quick-macos         # Build only macOS (simple)"
	@echo "  make quick-windows       # Build only Windows (simple)"
	@echo "  make quick-clean         # Clean and rebuild all (simple)"
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  install          - Install production dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint             - Run linting checks"
	@echo "  format           - Format code with black"
	@echo "  type-check       - Run type checking with mypy"
	@echo "  clean            - Clean build artifacts"
	@echo "  run              - Run the application"
	@echo ""
	@echo "🔢 Version Management:"
	@echo "  version-check        - Show current version"
	@echo "  version-patch        - Bump patch version (1.0.0 → 1.0.1)"
	@echo "  version-minor        - Bump minor version (1.0.0 → 1.1.0)"
	@echo "  version-major        - Bump major version (1.0.0 → 2.0.0)"
	@echo "  version-dry-run-*    - Preview version changes"
	@echo ""
	@echo "🚀 Release Commands:"
	@echo "  release-patch        - Bump patch version and trigger release"
	@echo "  release-minor        - Bump minor version and trigger release"
	@echo "  release-major        - Bump major version and trigger release"
	@echo ""
	@echo "📊 Utility Commands:"
	@echo "  docs             - Show documentation structure"
	@echo "  structure        - Show project structure"
	@echo "  dist-summary     - Show distribution summary"
	@echo "  build-status     - Show build status and logs"

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

# Enhanced build targets
build:
	@echo "🏗️  Starting Enhanced Unified Build..."
	python scripts/build/build_unified.py

build-quick:
	@echo "🚀 Starting Quick Build..."
	python build.py

build-macos:
	@echo "🍎 Building for macOS..."
	python scripts/build/build_unified.py --platform macos

build-windows:
	@echo "🪟 Building for Windows..."
	python scripts/build/build_unified.py --platform windows

build-clean:
	@echo "🧹 Clean build for all platforms..."
	python scripts/build/build_unified.py --clean

# Quick build targets (simple interface)
quick:
	python build.py

quick-macos:
	python build.py macos

quick-windows:
	python build.py windows

quick-clean:
	python build.py clean

# Legacy build targets (for compatibility)
dmg:
	python scripts/build/create_dmg.py

zip-windows:
	python scripts/build/create_windows_zip.py

# Clean targets
clean:
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf venv/
	rm -rf .pytest_cache/
	rm -rf htmlcov/

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
	@tree -I 'venv|__pycache__|*.egg-info|build' -L 3 || echo "Install 'tree' command for better output"

# Distribution summary
dist-summary:
	@echo "📦 Distribution Summary:"
	@echo "======================="
	@if [ -d "build/dist" ]; then \
		echo "📁 Location: build/dist/"; \
		echo "📊 Files:"; \
		find build/dist -name "*.dmg" -o -name "*.zip" -o -name "*.app" -o -name "*.exe" | while read file; do \
			size=$$(du -h "$$file" | cut -f1); \
			echo "   📁 $$(basename "$$file") ($$size)"; \
		done; \
		echo ""; \
		echo "📈 Total size:"; \
		du -sh build/dist/ | cut -f1 | xargs echo "   📊 Total:"; \
	else \
		echo "❌ No build directory found. Run 'make build' first."; \
	fi

# Build status and logs
build-status:
	@echo "🔍 Build Status:"
	@echo "==============="
	@if [ -d "build" ]; then \
		echo "📁 Build directory: build/"; \
		if [ -d "build/dist" ]; then \
			echo "✅ Distribution directory exists"; \
			find build/dist -name "*.dmg" -o -name "*.zip" -o -name "*.app" | wc -l | xargs echo "📦 Distribution files:"; \
		else \
			echo "❌ No distribution directory"; \
		fi; \
		if [ -d "build/logs" ]; then \
			echo "📄 Recent build logs:"; \
			ls -lt build/logs/*.log 2>/dev/null | head -5 | while read line; do \
				echo "   $$line"; \
			done; \
		else \
			echo "❌ No build logs found"; \
		fi; \
	else \
		echo "❌ No build directory found"; \
	fi

# Version management
version-patch:
	@echo "🔢 Bumping patch version..."
	python scripts/bump_version.py patch

version-minor:
	@echo "🔢 Bumping minor version..."
	python scripts/bump_version.py minor

version-major:
	@echo "🔢 Bumping major version..."
	python scripts/bump_version.py major

version-check:
	@echo "🔍 Current version:"
	@grep '^version = ' pyproject.toml

version-dry-run-patch:
	@echo "🔍 Patch version dry run:"
	python scripts/bump_version.py patch --dry-run

version-dry-run-minor:
	@echo "🔍 Minor version dry run:"
	python scripts/bump_version.py minor --dry-run

version-dry-run-major:
	@echo "🔍 Major version dry run:"
	python scripts/bump_version.py major --dry-run

# Release workflow (triggers both Windows and macOS builds)
release-patch: version-patch
	@echo "🚀 Creating patch release for all platforms..."
	git add pyproject.toml
	git commit -m "Bump version to $$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
	git push origin main
	@echo "✅ Patch release initiated. Check GitHub Actions for Windows and macOS build progress."

release-minor: version-minor
	@echo "🚀 Creating minor release for all platforms..."
	git add pyproject.toml
	git commit -m "Bump version to $$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
	git push origin main
	@echo "✅ Minor release initiated. Check GitHub Actions for Windows and macOS build progress."

release-major: version-major
	@echo "🚀 Creating major release for all platforms..."
	git add pyproject.toml
	git commit -m "Bump version to $$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
	git push origin main
	@echo "✅ Major release initiated. Check GitHub Actions for Windows and macOS build progress."

# Advanced build options
build-verbose:
	python scripts/build/build_unified.py --verbose

build-no-prereq:
	python scripts/build/build_unified.py --no-prereq-check

build-macos-app-only:
	python scripts/build/build_unified.py --platform macos --macos-only app

build-windows-exe-only:
	python scripts/build/build_unified.py --platform windows --windows-only exe

# Help for build system
build-help:
	@echo "🏗️  CSC-Reach Enhanced Build System"
	@echo "=================================="
	@echo ""
	@echo "The build system has been enhanced with:"
	@echo "• 🎯 Intelligent prerequisite checking"
	@echo "• 📊 Comprehensive build reporting"
	@echo "• 🔍 Detailed logging and error tracking"
	@echo "• ⚡ Parallel build support (future)"
	@echo "• 🧹 Smart cleaning with log preservation"
	@echo "• 📦 Automatic output verification"
	@echo ""
	@echo "For detailed options:"
	@echo "  python scripts/build/build_unified.py --help"
	@echo ""
	@echo "For quick building:"
	@echo "  python build.py --help"
