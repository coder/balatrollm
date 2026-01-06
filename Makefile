.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck quality all test

# Colors (ANSI)
YELLOW := \033[33m
GREEN  := \033[32m
BLUE   := \033[34m
RED    := \033[31m
RESET  := \033[0m

# Print helper
PRINT = printf "%b\n"

help: ## Show this help message
	@$(PRINT) "$(BLUE)BalatroLLM Development Makefile$(RESET)"
	@$(PRINT) ""
	@$(PRINT) "$(YELLOW)Available targets:$(RESET)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "help"      "Show this help message"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "install"   "Install dependencies"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "lint"      "Run ruff linter with auto-fixes"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "format"    "Run ruff formatter"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "typecheck" "Run type checker"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "quality"   "Run all code quality checks"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "all"       "Run all code quality checks and tests"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "test"      "Run all tests (unit + integration)"

install: ## Install dependencies
	@$(PRINT) "$(YELLOW)Installing all dependencies...$(RESET)"
	uv sync --group dev --group test

lint: ## Run ruff linter with auto-fixes
	@$(PRINT) "$(YELLOW)Running ruff linter...$(RESET)"
	ruff check --fix --select I .
	ruff check --fix .

format: ## Run ruff formatter
	@$(PRINT) "$(YELLOW)Running ruff formatter...$(RESET)"
	ruff check --select I --fix .
	ruff format .
	@$(PRINT) "$(YELLOW)Running mdformat formatter...$(RESET)"
	mdformat ./docs README.md CLAUDE.md

typecheck: ## Run type checker
	@$(PRINT) "$(YELLOW)Running Python type checker...$(RESET)"
	@ty check

quality: lint typecheck format ## Run all code quality checks
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"

test: ## Run all tests (unit first, then integration with parallelism)
	@$(PRINT) "$(YELLOW)Running tests/unit...$(RESET)"
	pytest tests/unit
	@$(PRINT) "$(YELLOW)Running tests/integration with 2 workers...$(RESET)"
	BALATROBOT_RENDER_ON_API=0 \
	BALATROBOT_HEADLESS=1 \
	pytest -n 2 tests/integration

all: lint format typecheck test ## Run all code quality checks and tests
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"
