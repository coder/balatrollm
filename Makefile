.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck quality setup teardown

# Colors for output
YELLOW := \033[33m
GREEN := \033[32m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Project variables
PYTHON := python
UV := uv
RUFF := ruff
TYPECHECK := basedpyright
RUNS ?= 5
INSTANCES ?= 1

help: ## Show this help message
	@echo "$(BLUE)BalatroLLM Development Makefile$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install dependencies
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	$(UV) sync --all-extras

# Code quality targets
lint: ## Run ruff linter with auto-fixes
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

quality: lint typecheck format ## Run all code quality checks
	@echo "$(GREEN)✓ All checks completed$(RESET)"

# Game targets
setup: ## Kill previous instances and start Balatro (INSTANCES=1)
	@echo "$(YELLOW)Stopping all previous instances...$(RESET)"
	@./balatro.sh --kill 2>/dev/null || true
	@echo "$(YELLOW)Starting Balatro with $(INSTANCES) instance(s)...$(RESET)"
	@ports=""; \
	for i in $$(seq 0 $$(($(INSTANCES) - 1))); do \
		port=$$((12346 + i)); \
		ports="$$ports -p $$port"; \
	done; \
	./balatro.sh $$ports

teardown: ## Stop Balatro processes
	@echo "$(YELLOW)Stopping Balatro...$(RESET)"
	@./balatro.sh --kill 2>/dev/null || true
	@echo "$(GREEN)✓ Services stopped$(RESET)"
