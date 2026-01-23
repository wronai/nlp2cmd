# =============================================================================
# NLP2CMD Makefile
# =============================================================================
# Usage:
#   make help          - Show this help
#   make install       - Install dependencies
#   make test          - Run all tests
#   make test-examples - Run all examples
#   make test-e2e      - Run E2E tests
#   make docker-build  - Build Docker images
#   make docker-up     - Start services
#   make docker-test   - Run tests in Docker
#   make docker-push   - Push Docker image to registry
#   make push          - Complete release (bump version + build + push Docker + PyPI)
#   make bump-patch    - Bump patch version (X.Y.Z -> X.Y.Z+1)
#   make bump-minor    - Bump minor version (X.Y.Z -> X.Y+1.0)
#   make bump-major    - Bump major version (X.Y.Z -> X+1.0.0)
#   make publish       - Publish to PyPI (with automatic patch bump)
# =============================================================================

.PHONY: help install test test-unit test-e2e lint format clean \
        docker-build docker-up docker-down docker-test docker-e2e docker-push \
        dev demo test-examples bump-patch bump-minor bump-major publish publish-test push

# Default target
.DEFAULT_GOAL := help

# Project settings
PROJECT_NAME := nlp2cmd
PYTHON := python3
PIP := pip3
PYTEST := pytest
DOCKER_COMPOSE := docker compose

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)NLP2CMD - Natural Language to Domain-Specific Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make install       # Install in development mode"
	@echo "  make test          # Run all tests"
	@echo "  make test-examples # Run all examples"
	@echo "  make docker-up     # Start Docker services"
	@echo "  make demo          # Run the demo"

# =============================================================================
# Development
# =============================================================================

install: ## Install package in development mode
	$(PIP) install -e ".[dev]" --break-system-packages

install-ci: ## Install for CI (no editable)
	$(PIP) install ".[dev]" --break-system-packages

deps: ## Install dependencies only
	$(PIP) install -r requirements.txt --break-system-packages

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	$(PYTEST) tests/ -v --tb=short

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v --tb=short

test-e2e: ## Run E2E tests only
	$(PYTEST) tests/e2e/ -v --tb=short

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ -v --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw tests/ -- -v --tb=short

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters (ruff, mypy)
	ruff check src/$(PROJECT_NAME)/ tests/
	mypy src/$(PROJECT_NAME)/ --ignore-missing-imports

format: ## Format code with ruff and black
	ruff format src/$(PROJECT_NAME)/ tests/
	black src/$(PROJECT_NAME)/ tests/

format-check: ## Check code formatting
	ruff format --check src/$(PROJECT_NAME)/ tests/
	black --check src/$(PROJECT_NAME)/ tests/

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker images
	$(DOCKER_COMPOSE) build

docker-build-no-cache: ## Build Docker images without cache
	$(DOCKER_COMPOSE) build --no-cache

docker-up: ## Start all services
	$(DOCKER_COMPOSE) up -d

docker-up-dev: ## Start development services
	$(DOCKER_COMPOSE) --profile dev up -d

docker-down: ## Stop all services
	$(DOCKER_COMPOSE) down

docker-down-v: ## Stop all services and remove volumes
	$(DOCKER_COMPOSE) down -v

docker-test: ## Run tests in Docker
	$(DOCKER_COMPOSE) --profile test run --rm nlp2cmd-test

docker-e2e: ## Run E2E tests in Docker
	$(DOCKER_COMPOSE) --profile e2e run --rm nlp2cmd-e2e

docker-logs: ## Show logs
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Open shell in container
	$(DOCKER_COMPOSE) exec nlp2cmd /bin/bash

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

docker-push: ## Push Docker image to registry
	@echo "$(YELLOW)Building Docker image...$(NC)"
	$(MAKE) docker-build
	@echo "$(YELLOW)Pushing Docker image...$(NC)"
	docker push nlp2cmd:latest
	docker push nlp2cmd:$(shell $(PYTHON) -c "import toml; content = toml.load(open('pyproject.toml')); print(content['project']['version'])")
	@echo "$(GREEN)Docker image pushed successfully!$(NC)"

# =============================================================================
# Development Utilities
# =============================================================================

demo: ## Run the end-to-end demo
	$(PYTHON) examples/architecture/end_to_end_demo.py

test-examples: ## Run all examples to test functionality
	@echo "$(BLUE)Testing all examples...$(NC)"
	@echo "$(YELLOW)Architecture examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/architecture/end_to_end_demo.py
	@echo ""
	@echo "$(YELLOW)Docker examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/docker/basic_docker.py
	PYTHONPATH=src $(PYTHON) examples/docker/file_repair.py
	@echo ""
	@echo "$(YELLOW)Kubernetes examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/kubernetes/basic_kubernetes.py
	@echo ""
	@echo "$(YELLOW)Pipeline examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/pipelines/infrastructure_health.py
	PYTHONPATH=src $(PYTHON) examples/pipelines/log_analysis.py
	@echo ""
	@echo "$(YELLOW)Shell examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/shell/basic_shell.py
	PYTHONPATH=src $(PYTHON) examples/shell/environment_analysis.py
	PYTHONPATH=src $(PYTHON) examples/shell/feedback_loop.py
	@echo ""
	@echo "$(YELLOW)SQL examples:$(NC)"
	@for file in examples/sql/*.py; do \
		if [ -f "$$file" ]; then \
			echo "Running $$file..."; \
			PYTHONPATH=src $(PYTHON) "$$file"; \
		fi; \
	done
	@echo ""
	@echo "$(YELLOW)Validation examples:$(NC)"
	PYTHONPATH=src $(PYTHON) examples/validation/config_validation.py
	@echo ""
	@echo "$(GREEN)All examples completed!$(NC)"

repl: ## Start interactive REPL
	$(PYTHON) -m $(PROJECT_NAME).cli

run-example: ## Run a specific example (usage: make run-example FILE=sql/basic_sql.py)
	$(PYTHON) examples/$(FILE)

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-docker: ## Clean Docker resources
	$(DOCKER_COMPOSE) down -v --rmi local
	docker system prune -f

clean-all: clean clean-docker ## Clean everything

# =============================================================================
# Release
# =============================================================================

build: clean ## Build package
	$(PYTHON) -m build

publish-test: build ## Publish to TestPyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

bump-patch: ## Bump patch version (X.Y.Z -> X.Y.Z+1)
	@echo "$(YELLOW)Bumping patch version...$(NC)"
	$(PYTHON) bump_version.py patch

bump-minor: ## Bump minor version (X.Y.Z -> X.Y+1.0)
	@echo "$(YELLOW)Bumping minor version...$(NC)"
	$(PYTHON) bump_version.py minor

bump-major: ## Bump major version (X.Y.Z -> X+1.0.0)
	@echo "$(YELLOW)Bumping major version...$(NC)"
	$(PYTHON) bump_version.py major

publish: build ## Publish to PyPI (with version bump)
	@echo "$(YELLOW)Bumping patch version...$(NC)"
	$(MAKE) bump-patch
	@echo "$(YELLOW)Rebuilding package with new version...$(NC)"
	$(MAKE) build
	@echo "$(YELLOW)Publishing to PyPI...$(NC)"
	$(PYTHON) -m twine upload dist/*

push: ## Complete release (bump version + build + push Docker + PyPI)
	@echo "$(YELLOW)Starting complete release process...$(NC)"
	@echo "$(YELLOW)1. Bumping patch version...$(NC)"
	$(MAKE) bump-patch
	@echo "$(YELLOW)2. Building package...$(NC)"
	$(MAKE) build
	@echo "$(YELLOW)3. Publishing to PyPI...$(NC)"
	$(PYTHON) -m twine upload dist/*
	@echo "$(YELLOW)4. Building and pushing Docker image...$(NC)"
	$(MAKE) docker-push
	@echo "$(GREEN)🎉 Complete release finished successfully!$(NC)"
	@echo "$(GREEN)   - Package published to PyPI$(NC)"
	@echo "$(GREEN)   - Docker image pushed to registry$(NC)"
	@echo "$(GREEN)   - Version bumped automatically$(NC)"

# =============================================================================
# Info
# =============================================================================

version: ## Show version
	@$(PYTHON) -c "import $(PROJECT_NAME); print($(PROJECT_NAME).__version__)"

info: ## Show project info
	@echo "$(BLUE)Project:$(NC) $(PROJECT_NAME)"
	@echo "$(BLUE)Python:$(NC) $(shell $(PYTHON) --version)"
	@echo "$(BLUE)Pip:$(NC) $(shell $(PIP) --version)"
	@echo "$(BLUE)Version:$(NC) $(shell $(PYTHON) -c 'import $(PROJECT_NAME); print($(PROJECT_NAME).__version__)')"
