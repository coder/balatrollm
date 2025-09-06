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
INSTANCES ?= 1

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

balatrobench: ## Run benchmark for all models and generate analysis (RUNS=5, INSTANCES=4)
	@$(eval BENCH_INSTANCES := $(if $(filter 1,$(INSTANCES)),4,$(INSTANCES)))
	@echo "$(YELLOW)Starting benchmark runs for all models ($(RUNS) runs each with $(BENCH_INSTANCES) instances)...$(RESET)"
	@ports=""; \
	for i in $$(seq 0 $$(($(BENCH_INSTANCES) - 1))); do \
		port=$$((12346 + i)); \
		ports="$$ports -p $$port"; \
	done; \
	echo "$(YELLOW)Running openai/gpt-oss-120b...$(RESET)"; \
	balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model openai/gpt-oss-120b $$ports || true; \
	echo "$(YELLOW)Running openai/gpt-oss-20b...$(RESET)"; \
	balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model openai/gpt-oss-20b $$ports || true; \
	echo "$(YELLOW)Running qwen/qwen3-235b-a22b-thinking-2507...$(RESET)"; \
	balatrollm --runs-dir ./balatrobench --runs $(RUNS) --model qwen/qwen3-235b-a22b-thinking-2507 $$ports || true; \
	echo "$(YELLOW)Generating benchmark analysis...$(RESET)"; \
	balatrollm benchmark --runs-dir balatrobench/runs --output-dir balatrobench/benchmarks; \
	echo "$(GREEN)✓ Benchmark completed$(RESET)"
