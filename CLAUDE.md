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
```bash
balatrollm                                        # Default settings (cerebras-qwen3-235b)
balatrollm --model groq-qwen3-32b                 # Specific model
balatrollm --strategy aggressive                 # Built-in strategy
balatrollm --strategy /path/to/custom/strategy     # External strategy directory
balatrollm --strategy ../my-strategies/experimental # Relative path to strategy
balatrollm --list-models                          # List available models
balatrollm --verbose                              # Enable verbose logging
balatrollm --base-url http://localhost:4000 --api-key your-key
```

### Development
```bash
make dev           # Quick check (format + lint + typecheck)
make all           # Complete quality check
make test          # Run tests
make test-cov      # Run tests with coverage
make clean         # Remove build artifacts
make start         # Kill previous instances and start LiteLLM + Balatro
```

## Architecture

**LLMBot (`src/balatrollm/bot.py`)**: Main bot class with Config integration, StrategyManager, LLM decision-making, response history tracking, BalatroClient integration, proxy validation, model validation, and project version management.

**CLI Entry Point (`src/balatrollm/__init__.py`)**: Command-line interface with argument parsing, environment variable support, configuration validation, and async game execution.

**Configuration (`src/balatrollm/config.py`)**: Config dataclass handling model settings, proxy URLs, bot parameters, and environment variable loading.

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
- **Cerebras**: cerebras-qwen3-235b (default), cerebras-gpt-oss-120b, cerebras-gpt-oss-20b
- **Groq**: groq-qwen3-32b
- **Local**: LM Studio integration

**Environment Variables**:
- `CEREBRAS_API_KEY`, `GROQ_API_KEY`
- `LITELLM_MODEL` (default: cerebras-qwen3-235b)
- `LITELLM_BASE_URL` (default: http://localhost:4000)
- `LITELLM_API_KEY` (default: sk-balatrollm-proxy-key)
- `BALATROLLM_STRATEGY` (default: default)

## Code Quality

Uses Ruff (linting/formatting), basedpyright (type checking), pytest (testing), conventional commits, and Release Please automation.

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

- `runs/[version]/[model]/[strategy]/[timestamp]_[deck]_[seed].jsonl`
- JSONL format for performance analysis across models and strategies

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
