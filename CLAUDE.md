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
usage: balatrollm [-h] [--model MODEL] [--base-url BASE_URL]
                  [--api-key API_KEY] [--list-models]
                  [--litellm-config LITELLM_CONFIG] [--strategy STRATEGY]
                  [--verbose] [--config CONFIG]
                  {benchmark} ...

LLM-powered Balatro bot using LiteLLM proxy

positional arguments:
  {benchmark}           Available commands
    benchmark           Analyze runs and generate leaderboards

options:
  -h, --help            show this help message and exit
  --model MODEL         Model name to use from LiteLLM proxy (default:
                        cerebras/gpt-oss-120b)
  --base-url BASE_URL   LiteLLM base URL (default: http://localhost:4000)
  --api-key API_KEY     LiteLLM proxy API key (default: sk-balatrollm-proxy-
                        key)
  --list-models         List available models from the proxy and exit
  --litellm-config LITELLM_CONFIG
                        Path to LiteLLM configuration file (default:
                        config/litellm.yaml)
  --strategy STRATEGY   Strategy to use. Can be a built-in strategy name
                        (default, aggressive) or a path to a strategy
                        directory (default: default)
  --verbose, -v         Enable verbose logging
  --config CONFIG       Load configuration from a previous run's config.json
                        file

Examples:
  balatrollm --model cerebras/gpt-oss-120b
  balatrollm --model groq/qwen/qwen3-32b --base-url http://localhost:4000
  balatrollm --strategy aggressive
  balatrollm --strategy path/to/my/strategy/directory
  balatrollm --list-models
  balatrollm --config runs/version/provider/model/strategy/run/config.json
  balatrollm benchmark --runs-dir runs --output-dir benchmark_results
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

**LLMBot (`src/balatrollm/bot.py`)**: Main bot class with Config integration, StrategyManager, LLM decision-making, response history tracking, BalatroClient integration, proxy validation, model validation, and project version management.

**CLI Entry Point (`src/balatrollm/__init__.py`)**: Command-line interface with argument parsing, configuration validation, and async game execution.

**Configuration (`src/balatrollm/config.py`)**: Config dataclass handling model settings and bot parameters. Base URLs and API keys use CLI defaults for security.

**Strategy System (`src/balatrollm/strategies.py`)**: StrategyManager class for Jinja2-based strategy templates and tool loading.

**Data Collection (`src/balatrollm/data_collection.py`)**: RunDataCollector for game execution logging, performance tracking, and run data organization.

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

1. Validate proxy connection and model availability
2. Game loop: Get state → Render strategy templates → Send to LLM → Parse response → Execute action
3. Handle different states: BLIND_SELECT, SELECTING_HAND, SHOP, ROUND_EVAL

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
runs/                              # Game execution logs (organized by version/model/strategy)
tests/test_llm.py                  # Test suite
```

## Context7 Library IDs

**Core**: `/s1m0n38/balatrobot`, `/pallets/jinja`, `/openai/openai-python`, `/berriai/litellm`, `/encode/httpx`
**Dev**: `/detachhead/basedpyright`, `/pytest-dev/pytest`, `/pytest-dev/pytest-asyncio`, `/astral-sh/ruff`, `/astral-sh/uv`

## Results Tracking

- `runs/[version]/[provider]/[model-name]/[strategy]/[timestamp]_[deck]_[seed].jsonl`
- JSONL format for performance analysis across providers, models, and strategies
- Provider/model parsing: `groq/qwen/qwen3-32b` → `groq/qwen--qwen3-32b` (filesystem safe)
- Enables grouping by provider (e.g., all Cerebras models) or specific model comparisons

## Strategy System

The `--strategy` flag accepts either built-in strategy names or paths to custom strategy directories:

**Built-in Strategies**:

- **Default** (`--strategy default`): Conservative, financially disciplined approach
- **Aggressive** (`--strategy aggressive`): High-risk, high-reward approach with aggressive spending

**Custom Strategy Paths**:

- Absolute paths: `--strategy /path/to/my/custom/strategy`
- Relative paths: `--strategy ../custom-strategies/experimental`
- The system will automatically resolve built-in strategy names first, then fall back to path resolution

Each strategy directory must contain:

- `STRATEGY.md.jinja`: Strategy-specific guide
- `GAMESTATE.md.jinja`: Game state representation
- `MEMORY.md.jinja`: Response history tracking
- `TOOLS.json`: Strategy-specific function definitions
