.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck quality fixtures test all

# Colors for output
YELLOW := \033[33m
GREEN := \033[32m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Test variables
PYTEST_MARKER ?=

# OS detection for balatro launcher script
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)
ifeq ($(UNAME_S),Darwin)
    BALATRO_SCRIPT := python scripts/balatro-macos.py
else ifeq ($(UNAME_S),Linux)
    BALATRO_SCRIPT := python scripts/balatro-linux.py
else
    BALATRO_SCRIPT := python scripts/balatro-windows.py
endif

help: ## Show this help message
	@echo "$(BLUE)BalatroLLM Development Makefile$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install dependencies
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	uv sync --all-extras

# Code quality targets
lint: ## Run ruff linter with auto-fixes
	@echo "$(YELLOW)Running ruff linter...$(RESET)"
	ruff check --fix --select I .
	ruff check --fix .

format: ## Run ruff formatter
	@echo "$(YELLOW)Running ruff formatter...$(RESET)"
	ruff check --select I --fix .
	ruff format .
	@echo "$(YELLOW)Running mdformat formatter...$(RESET)"
	mdformat ./docs README.md CLAUDE.md

typecheck: ## Run type checker
	@echo "$(YELLOW)Running type checker...$(RESET)"
	basedpyright src/ tests/

quality: lint typecheck format ## Run all code quality checks
	@echo "$(GREEN)✓ All checks completed$(RESET)"

fixtures: ## Generate fixtures
	@echo "$(YELLOW)Starting Balatro...$(RESET)"
	$(BALATRO_SCRIPT) --fast --debug
	@echo "$(YELLOW)Generating all fixtures...$(RESET)"
	python tests/fixtures/generate.py

test: ## Run tests head-less
	@echo "$(YELLOW)Starting Balatro...$(RESET)"
	$(BALATRO_SCRIPT) --fast --debug
	@echo "$(YELLOW)Running tests...$(RESET)"
	pytest tests/lua $(if $(PYTEST_MARKER),-m "$(PYTEST_MARKER)") -v -s

all: lint format typecheck test ## Run all code quality checks and tests
	@echo "$(GREEN)✓ All checks completed$(RESET)"
