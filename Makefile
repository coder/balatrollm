.DEFAULT_GOAL := help
.PHONY: help install install-dev lint lint-fix format typecheck test test-cov quality clean setup teardown all balatrobench

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
RUNS ?= 5

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

quality: lint typecheck format ## Run all code quality checks
	@echo "$(GREEN)✓ All checks completed$(RESET)"

# Test targets
test: ## Run tests
	@echo "$(YELLOW)Running tests...$(RESET)"
	pytest

test-cov: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(RESET)"
	pytest --cov=src/balatrollm --cov-report=term-missing --cov-report=html

all: lint format typecheck test ## Run all code quality checks and tests
	@echo "$(GREEN)✓ All checks completed$(RESET)"

# Build targets
clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

# Game targets
setup: ## Kill previous instances and start LiteLLM server + Balatro
	@echo "$(YELLOW)Stopping all previous instances...$(RESET)"
	@pkill -f litellm 2>/dev/null || true
	@./balatro.sh --kill 2>/dev/null || true
	@echo "$(YELLOW)Starting LiteLLM proxy server...$(RESET)"
	@litellm --config config/litellm.yaml &
	@sleep 3
	@echo "$(YELLOW)Starting Balatro...$(RESET)"
	@./balatro.sh

teardown: ## Stop LiteLLM server and Balatro processes
	@echo "$(YELLOW)Stopping LiteLLM proxy server...$(RESET)"
	@pkill -f litellm 2>/dev/null || true
	@echo "$(YELLOW)Stopping Balatro...$(RESET)"
	@./balatro.sh --kill 2>/dev/null || true
	@echo "$(GREEN)✓ Services stopped$(RESET)"

balatrobench: ## Run benchmark for all models and generate analysis (RUNS=5)
	@echo "$(YELLOW)Starting benchmark runs for all models ($(RUNS) runs each)...$(RESET)"
	@echo "$(YELLOW)Running cerebras/gpt-oss-120b...$(RESET)"
	@balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model cerebras/gpt-oss-120b || true
	@echo "$(YELLOW)Running cerebras/qwen-3-235b-a22b-thinking-2507...$(RESET)"
	@balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model cerebras/qwen-3-235b-a22b-thinking-2507 || true
	@echo "$(YELLOW)Running cerebras/qwen-3-235b-a22b-instruct-2507...$(RESET)"
	@balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model cerebras/qwen-3-235b-a22b-instruct-2507 || true
	@echo "$(YELLOW)Running groq/openai/gpt-oss-20b...$(RESET)"
	@balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model groq/openai/gpt-oss-20b || true
	@echo "$(YELLOW)Generating benchmark analysis...$(RESET)"
	@balatrollm benchmark --runs-dir balatrobench/runs --output-dir balatrobench/benchmarks
	@echo "$(GREEN)✓ Benchmark completed$(RESET)"
