# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Balatrollm is an LLM-powered bot that plays Balatro (a roguelike poker deck-building game) using the BalatroBot client. The bot uses LiteLLM proxy to communicate with various LLM providers and makes strategic decisions based on game state analysis.

## Development Commands

### Environment Setup

```bash
# Install dependencies (including dev dependencies)
uv sync --all-extras --group dev

# Create environment configuration
cp .envrc.example .envrc
source .envrc
```

### LiteLLM Proxy

```bash
# Start the LiteLLM proxy server (required before running the bot)
litellm --config config/litellm.yaml
```

### Running the Application

```bash
# Run with default settings
balatrollm

# Run with specific model
balatrollm --model groq-qwen3-32b

# List available models from proxy
balatrollm --list-models

# Enable verbose logging
balatrollm --verbose
```

### Development Quality Commands

```bash
# Run all quality checks
make all

# Individual quality checks
make lint          # Run ruff linter (check only)
make lint-fix      # Run ruff linter with auto-fixes
make format        # Run ruff formatter
make typecheck     # Run basedpyright type checker

# Development workflow
make dev           # Quick development check (format + lint + typecheck)

# Cleanup
make clean         # Remove build artifacts and caches
```

### Testing

```bash
# Run tests (using pytest)
pytest

# Run specific test file
pytest tests/test_example.py
```

## Architecture

### Core Components

**LLMBot (`src/balatrollm/llm.py`)**
- Main bot implementation that orchestrates game play
- Manages LiteLLM client connection and model validation
- Handles game state analysis and decision making through LLM
- Executes actions via BalatroClient integration
- Uses Jinja2 templates for prompt generation

**CLI Entry Point (`src/balatrollm/__init__.py`)**
- Command-line interface with argument parsing
- Environment variable support for configuration
- Proxy connection validation and error handling
- Async game execution wrapper

**Template System (`src/balatrollm/templates/`)**
- `system.md.jinja`: Comprehensive Balatro strategy guide and rules
- `game_state.md.jinja`: Dynamic game state representation for LLM analysis
- Templates use Jinja2 with custom filters (e.g., `from_json`)

**Tools Configuration (`src/balatrollm/tools.json`)**
- OpenAI function calling definitions for different game states
- Maps game states (BLIND_SELECT, SELECTING_HAND, SHOP) to available actions
- Defines function schemas for LLM tool use

### Key Dependencies

- **balatrobot**: Core Balatro game client (from git repository)
- **litellm**: LLM proxy server for multiple providers
- **openai**: OpenAI client for LLM communication
- **jinja2**: Template engine for prompt generation
- **httpx**: HTTP client for proxy health checks

### Game Integration Flow

1. **Initialization**: Validate LiteLLM proxy connection and model availability
2. **Game Loop**:
   - Get current game state from BalatroClient
   - Render game state using Jinja2 templates
   - Send context to LLM with state-specific tools
   - Parse LLM tool call response
   - Execute action through BalatroClient
3. **State Handling**: Different logic for BLIND_SELECT, SELECTING_HAND, SHOP, ROUND_EVAL states

### LiteLLM Configuration

The `config/litellm.yaml` defines available models:
- **Cerebras**: High-performance cloud inference (gpt-oss-120b, gpt-oss-20b)
- **Groq**: Fast inference with Qwen models
- **Local**: LM Studio integration for development

Environment variables required:
- `CEREBRAS_API_KEY`: For Cerebras models
- `GROQ_API_KEY`: For Groq models

## Development Guidelines

### Code Quality
- Uses Ruff for linting and formatting with import sorting
- Uses basedpyright for type checking in basic mode
- Follows conventional commits specification
- Automated release process with Release Please

### Project Structure

```
src/balatrollm/
├── __init__.py             # CLI entry point and argument parsing
├── llm.py                  # Core LLMBot implementation
├── tools.json              # OpenAI function definitions by game state
└── templates/
    ├── system.md.jinja     # Comprehensive game strategy guide
    └── game_state.md.jinja # Dynamic game state representation
```

### Template System Usage

- Templates handle complex game state rendering for LLM context
- System template contains extensive Balatro strategy documentation
- Game state template dynamically formats current game information
- Custom Jinja2 filter `from_json` for JSON parsing in templates

### Error Handling Patterns

- Proxy connection validation before game start
- Model availability checking with fallback suggestions
- Graceful keyboard interrupt handling
- Comprehensive logging with different verbosity levels

## Dependency Documentation

When working with code that uses these dependencies, search their documentation using Context7 MCP server (`--c7` flag) with these library IDs:

**Core Dependencies:**

- **balatrobot**: `/s1m0n38/balatrobot`
- **jinja2**: `/pallets/jinja`
- **openai**: `/openai/openai-python`
- **litellm**: `/berriai/litellm`
- **httpx**: `/encode/httpx`

**Dev Dependencies:**

- **basedpyright**: `/detachhead/basedpyright`
- **pytest**: `/pytest-dev/pytest`
- **pytest-asyncio**: `/pytest-dev/pytest-asyncio`
- **ruff**: `/astral-sh/ruff`
- **uv**: `/astral-sh/uv`

**Usage:** When implementing features or fixing issues related to any of these libraries, use the Context7 MCP server to get up-to-date documentation and code examples.

## Important Notes

- The bot currently has LLM decision-making enabled only for SELECTING_HAND state
- BLIND_SELECT and SHOP states use hardcoded actions (TODOs indicate future LLM integration)
- Game state management relies on BalatroClient state machine
- LiteLLM proxy must be running before starting the bot
- Response history is maintained for context in subsequent LLM calls
