# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BalatroLLM is an LLM-powered bot that plays Balatro (a roguelike poker deck-building game) using the BalatroBot client. The bot uses OpenAI-compatible APIs to communicate with various LLM providers and makes strategic decisions based on game state analysis.

## Development Commands

### Environment Setup

```bash
uv sync --all-extras --group dev
cp .envrc.example .envrc
# edit .envrc with your OpenRouter API key
source .envrc
```

### Running the Application

**balatrollm** - Main bot CLI:

```
usage: balatrollm [-h] [-m MODEL] [-l] [-s STRATEGY] [-u BASE_URL]
                  [-k API_KEY] [-d RUNS_DIR] [-r RUNS_PER_SEED]
                  [--seeds SEEDS] [-p PORTS] [--no-screenshot]
                  [--use-default-paths]

LLM-powered Balatro bot

options:
  -h, --help            show this help message and exit
  -m, --model MODEL     Model name to use from OpenAI-compatible API (required, uses BALATROLLM_MODEL env var if set)
  -l, --list-models     List available models from OpenAI-compatible API and exit
  -s, --strategy STRATEGY
                        Name of the strategy to use (default: default)
  -u, --base-url BASE_URL
                        OpenAI-compatible API base URL (required, uses BALATROLLM_BASE_URL env var if set)
  -k, --api-key API_KEY
                        API key (default: BALATROLLM_API_KEY env var)
  -d, --runs-dir RUNS_DIR
                        Base directory for storing run data (default: current directory)
  -r, --runs-per-seed RUNS_PER_SEED
                        Number of runs per seed (default: 1)
  --seeds SEEDS         Comma-separated list of seeds (e.g., AAAA123,BBBB456,CCCC789)
  -p, --ports PORTS     Comma-separated list of ports for BalatroBot client connections (default: 12346, e.g., 12346,12347,12348)
  --no-screenshot       Disable taking screenshots during gameplay
  --use-default-paths   Use BalatroBot's default storage paths for screenshots and game logs
```

**balatrobench** - Benchmark analysis CLI:

```
usage: balatrobench [-h] (--models | --strategies) [--input-dir INPUT_DIR]
                    [--output-dir OUTPUT_DIR] [--avif]

Analyze BalatroLLM runs and generate benchmark leaderboards

options:
  -h, --help            show this help message and exit
  --models              Analyze by models (compare models within strategies)
  --strategies          Analyze by strategies (compare strategies for each model)
  --input-dir INPUT_DIR
                        Input directory with run data (default: runs/v{version})
  --output-dir OUTPUT_DIR
                        Output directory for benchmark results (default: benchmarks/[models|strategies]/v{version})
  --avif                Convert PNG screenshots to AVIF format after analysis
```

### Development

```
BalatroLLM Development Makefile

Available targets:
  help               Show this help message
  install            Install dependencies
  lint               Run ruff linter with auto-fixes
  format             Run ruff formatter
  typecheck          Run type checker
  quality            Run all code quality checks
  setup              Kill previous instances and start Balatro (INSTANCES=1)
  teardown           Stop Balatro processes
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

**Key Dependencies**: balatrobot, openai, jinja2, httpx

**Game Flow**:

1. Initialize game with run directory and data collection setup
2. Main game loop: Get state → Render strategy templates → Send to LLM with retry logic → Parse response → Execute action
3. Handle game states: BLIND_SELECT, SELECTING_HAND, SHOP, ROUND_EVAL, GAME_OVER
4. Collect comprehensive statistics and generate run reports

**Available Models** (via OpenRouter):

- **OpenAI**: openai/gpt-oss-20b (default), openai/gpt-oss-120b
- **Qwen**: qwen/qwen3-235b-a22b-thinking-2507, qwen/qwen3-235b-a22b-2507
- **X-AI**: x-ai/grok-code-fast-1
- **Google**: google/gemini-2.5-flash

**API Key**:

- `OPENROUTER_API_KEY` (provides access to all providers)

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

**Core**: `/coder/balatrobot`, `/pallets/jinja`, `/openai/openai-python`, `/encode/httpx`
**Dev**: `/detachhead/basedpyright`, `/pytest-dev/pytest`, `/pytest-dev/pytest-asyncio`, `/astral-sh/ruff`, `/astral-sh/uv`

## Results Tracking

**Run Data Structure:**

- `runs/v{version}/{strategy}/{vendor}/{model}/{timestamp}_{deck}_s{stake}_{seed}/`
- Each run directory contains: config.json, strategy.json, stats.json, gamestates.jsonl, requests.jsonl, responses.jsonl, run.log, screenshots/
- Strategy-first organization enables easy comparison across vendors/models within strategies

**Benchmark Results Structure (Dual Modes):**

Benchmarks can be generated in two modes using the `balatrobench` CLI:

**By Models Mode** (`--models`):
- `benchmarks/models/v{version}/{strategy}/leaderboard.json` - Models ranked within each strategy
- `benchmarks/models/v{version}/{vendor}/{model}/{strategy}/stats.json` - Detailed model stats per strategy
- Compare different models within each strategy

**By Strategies Mode** (`--strategies`):
- `benchmarks/strategies/v{version}/{strategy}/leaderboard.json` - Models ranked within strategy
- `benchmarks/strategies/v{version}/{vendor}/{model}.json` - Model stats across strategies
- Compare different strategies for each model

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
