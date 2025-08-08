.DEFAULT_GOAL := help
.PHONY: help install install-dev lint lint-fix format typecheck quality clean all dev

# Colors for output
YELLOW := \033[33m
GREEN := \033[32m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Project variables
PYTHON := python3
UV := uv
RUFF := ruff
TYPECHECK := basedpyright

help: ## Show this help message
	@echo "$(BLUE)BalatroLLM Development Makefile$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install package dependencies
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	$(UV) sync

install-dev: ## Install package with development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	$(UV) sync --all-extras --group dev

# Code quality targets
lint: ## Run ruff linter (check only)
	@echo "$(YELLOW)Running ruff linter...$(RESET)"
	$(RUFF) check --select I .
	$(RUFF) check .

lint-fix: ## Run ruff linter with auto-fixes
	@echo "$(YELLOW)Running ruff linter with fixes...$(RESET)"
	$(RUFF) check --select I --fix .
	$(RUFF) check --fix .

format: ## Run ruff formatter
	@echo "$(YELLOW)Running ruff formatter...$(RESET)"
	$(RUFF) check --select I --fix .
	$(RUFF) format .

typecheck: ## Run type checker
	@echo "$(YELLOW)Running type checker...$(RESET)"
	$(TYPECHECK)

quality: lint format typecheck ## Run all code quality checks
	@echo "$(GREEN)✓ All quality checks completed$(RESET)"

# Build targets
clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

# Convenience targets
dev: format lint typecheck ## Quick development check
	@echo "$(GREEN)✓ Development checks completed$(RESET)"

all: format lint typecheck ## Complete quality check
	@echo "$(GREEN)✓ All checks completed successfully$(RESET)"
