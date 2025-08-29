# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BalatroLLM is an LLM-powered bot that plays Balatro (a roguelike poker deck-building game) using the BalatroBot client. The bot uses LiteLLM proxy to communicate with various LLM providers and makes strategic decisions based on game state analysis.

## Development Commands

### Environment Setup

```bash
uv sync --all-extras --group dev
cp .envrc.example .envrc
source .envrc
```

### LiteLLM Proxy

```bash
litellm --config config/litellm.yaml
```

### Running the Application

```
usage: balatrollm [-h] [--model MODEL] [--list-models] [--strategy STRATEGY]
                  [--base-url BASE_URL] [--api-key API_KEY] [--config CONFIG]
                  {benchmark} ...

LLM-powered Balatro bot using LiteLLM proxy

positional arguments:
  {benchmark}          Available commands
    benchmark          Analyze runs and generate leaderboards

options:
  -h, --help           show this help message and exit
  --model MODEL        Model name to use from LiteLLM proxy (default:
                       cerebras/gpt-oss-120b)
  --list-models        List available models from the proxy and exit
  --strategy STRATEGY  Name of the strategy to use (default: default)
  --base-url BASE_URL  LiteLLM base URL (default: http://localhost:4000)
  --api-key API_KEY    LiteLLM proxy API key (default: sk-balatrollm-proxy-
                       key)
  --config CONFIG      Load configuration from a previous run's config.json
                       file

Examples:
  balatrollm --model cerebras/gpt-oss-120b
  balatrollm --model groq/qwen/qwen3-32b --base-url http://localhost:4000
  balatrollm --strategy aggressive
  balatrollm --list-models
  balatrollm --config runs/v0.3.0/default/cerebras/gpt-oss-120b/20240101_120000_RedDeck_s1_OOOO155/config.json
  balatrollm benchmark --runs-dir runs --output-dir benchmarks
```

### Development

```
BalatroLLM Development Makefile

Available targets:
  help               Show this help message
  install            Install package dependencies
  install-dev        Install package with development dependencies
  lint               Run ruff linter (check only)
  lint-fix           Run ruff linter with auto-fixes
  format             Run ruff formatter
  typecheck          Run type checker
  quality            Run all code quality checks
  test               Run tests
  test-cov           Run tests with coverage report
  all                Run all code quality checks and tests
  clean              Clean build artifacts and caches
  setup              Kill previous instances and start LiteLLM server + Balatro
  teardown           Stop LiteLLM server and Balatro processes
```

### Game Automation

```
Usage: ./balatro.sh [OPTIONS]
       ./balatro.sh -p PORT [OPTIONS]
       ./balatro.sh --kill
       ./balatro.sh --status

Options:
  -p, --port PORT  Specify port for Balatro instance (can be used multiple times)
                   Default: 12346 if no port specified
  --headless       Enable headless mode (sets BALATROBOT_HEADLESS=1)
  --fast           Enable fast mode (sets BALATROBOT_FAST=1)
  --audio          Enable audio (disabled by default, sets BALATROBOT_AUDIO=1)
  --kill           Kill all running Balatro instances and exit
  --status         Show information about running Balatro instances
  -h, --help       Show this help message

Examples:
  ./balatro.sh                            # Start single instance on default port 12346
  ./balatro.sh -p 12347                   # Start single instance on port 12347
  ./balatro.sh -p 12346 -p 12347          # Start two instances on ports 12346 and 12347
  ./balatro.sh --headless --fast          # Start with headless and fast mode on default port
  ./balatro.sh --audio                    # Start with audio enabled on default port
  ./balatro.sh --kill                     # Kill all running Balatro instances
  ./balatro.sh --status                   # Show running instances
```

## Architecture

**LLMBot (`src/balatrollm/bot.py`)**: Main bot class with clean architecture featuring Config integration, StrategyManager for template rendering, LLM decision-making with retry logic, response history tracking, and BalatroClient integration.

**CLI Entry Point (`src/balatrollm/__init__.py`)**: Simplified command-line interface with argument parsing and async game execution using modern Python patterns.

**Configuration (`src/balatrollm/config.py`)**: Config dataclass with metadata fields (name, description, author, tags) for enhanced run tracking and version management.

**Strategy System (`src/balatrollm/strategies.py`)**: Lightweight StrategyManager class for managing Jinja2-based strategy templates with built-in strategy support only.

**Data Collection (`src/balatrollm/data_collection.py`)**: RunStatsCollector for structured game execution logging, comprehensive performance tracking, and organized run data storage.

**Benchmarking (`src/balatrollm/benchmark.py`)**: Comprehensive benchmark analysis system with aggregated statistics, leaderboard generation, and hierarchical result organization.

**Strategies (`src/balatrollm/strategies/`)**: Strategy-based organization:

- `default/`: Conservative strategy (financial discipline)
- `aggressive/`: High-risk, high-reward strategy

Each strategy contains:

- `STRATEGY.md.jinja`: Strategy-specific guide
- `GAMESTATE.md.jinja`: Game state representation
- `MEMORY.md.jinja`: Response history tracking
- `TOOLS.json`: Strategy-specific function definitions

**Key Dependencies**: balatrobot, litellm, openai, jinja2, httpx

**Game Flow**:

1. Initialize game with run directory and data collection setup
2. Main game loop: Get state → Render strategy templates → Send to LLM with retry logic → Parse response → Execute action
3. Handle game states: BLIND_SELECT, SELECTING_HAND, SHOP, ROUND_EVAL, GAME_OVER
4. Collect comprehensive statistics and generate run reports

**Available Models** (`config/litellm.yaml`):

- **Cerebras**: cerebras/gpt-oss-120b (default), cerebras/gpt-oss-20b, cerebras/qwen-3-235b-a22b-thinking-2507
- **Groq**: groq/qwen/qwen3-32b
- **Local**: lmstudio/deepseek-r1-0528-qwen3-8b

**Provider API Keys** (required by LiteLLM or direct provider access):

- `CEREBRAS_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

## Code Quality

Uses Ruff (linting/formatting), basedpyright (type checking), pytest (testing), conventional commits, and Release Please automation.

**Modern Type Hints**: Use built-in types for Python 3.9+ instead of typing module equivalents:

- Use `dict` instead of `Dict`
- Use `list` instead of `List`
- Use `tuple` instead of `Tuple`
- Use `set` instead of `Set`
- Use `str | None` instead of `Optional[str]`
- Use `int | str` instead of `Union[int, str]`

## Project Structure

```
src/balatrollm/
├── __init__.py                    # CLI entry point with argument parsing
├── bot.py                         # Main LLMBot class with game logic
├── config.py                      # Configuration dataclass
├── strategies.py                  # StrategyManager for Jinja2 templates
├── data_collection.py             # RunDataCollector for game logging
└── strategies/                    # Strategy-based templates
    ├── default/                   # Conservative strategy
    └── aggressive/                # High-risk strategy
        ├── STRATEGY.md.jinja      # Strategy guide
        ├── GAMESTATE.md.jinja     # Game state representation
        ├── MEMORY.md.jinja        # Response history
        └── TOOLS.json             # Function definitions

balatro.sh                         # Game automation script
runs/                              # Game execution logs (organized by version/strategy/provider/model)
benchmarks/                        # Benchmark results (organized by version/strategy/provider/model)
tests/test_llm.py                  # Test suite
```

## Context7 Library IDs

**Core**: `/s1m0n38/balatrobot`, `/pallets/jinja`, `/openai/openai-python`, `/berriai/litellm`, `/encode/httpx`
**Dev**: `/detachhead/basedpyright`, `/pytest-dev/pytest`, `/pytest-dev/pytest-asyncio`, `/astral-sh/ruff`, `/astral-sh/uv`

## Results Tracking

**Run Data Structure:**

- `runs/[version]/[strategy]/[provider]/[model-name]/[timestamp]_[deck]_[seed]/`
- JSONL format for performance analysis across providers, models, and strategies
- Provider/model parsing: `groq/qwen/qwen3-32b` → `groq/qwen--qwen3-32b` (filesystem safe)
- Strategy-first organization enables easy comparison across providers/models within strategies

**Benchmark Results Structure:**

- `benchmarks/[version]/[strategy]/[provider]/[model-name].json` - Detailed model analysis
- `benchmarks/[version]/[strategy]/leaderboard.json` - Strategy-specific leaderboard
- Hierarchical structure matches runs organization for consistency

## Strategy System

The `--strategy` flag accepts built-in strategy names:

**Built-in Strategies**:

- **Default** (`--strategy default`): Conservative, financially disciplined approach
- **Aggressive** (`--strategy aggressive`): High-risk, high-reward approach with aggressive spending

Each strategy directory must contain:

- `STRATEGY.md.jinja`: Strategy-specific guide
- `GAMESTATE.md.jinja`: Game state representation
- `MEMORY.md.jinja`: Response history tracking
- `TOOLS.json`: Strategy-specific function definitions
