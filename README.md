<div align="center">
  <h1>BalatroLLM</h1>
  <p align="center">
    <a href="https://github.com/S1M0N38/balatrollm/releases">
      <img alt="GitHub release" src="https://img.shields.io/github/v/release/S1M0N38/balatrollm?include_prereleases&sort=semver&style=for-the-badge&logo=github"/>
    </a>
    <a href="https://discord.gg/TPn6FYgGPv">
      <img alt="Discord" src="https://img.shields.io/badge/discord-server?style=for-the-badge&logo=discord&logoColor=%23FFFFFF&color=%235865F2"/>
    </a>
  </p>
  <p><em>A Balatro bot powered by LLMs</em></p>
</div>

______________________________________________________________________

## Overview

BalatroLLM is a bot that uses Large Language Models (LLMs) to play [Balatro](https://www.playbalatro.com/), the popular roguelike poker deck-building game. The bot analyzes game states, makes strategic decisions, and executes actions through the [BalatroBot](https://github.com/S1M0N38/balatrobot) client.

The system combines multiple components to make informed decisions:

- **Strategy templates** (`STRATEGY.md.jinja`) - Define playing style and approach
- **Game state analysis** (`GAMESTATE.md.jinja`) - Current game situation and available options
- **Memory system** (`MEMORY.md.jinja`) - Historical context from previous decisions
- **Action tools** (`TOOLS.json`) - Available game actions and their parameters

These components are processed together in a single LLM call, enabling the bot to understand the current situation and choose the optimal action based on its configured strategy.

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) package manager
- Balatro instance with [BalatroBot](https://github.com/S1M0N38/balatrobot) mod installed

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/S1M0N38/balatrollm.git
cd balatrollm

# 2. Create and activate environment
uv sync

# 3. Configure environment
cp .envrc.example .envrc
# edit .envrc with your API keys

# 4. Activate environment
source .envrc
```

#### Environment Variables

**Provider API Keys** (required by LiteLLM or direct provider access)

```bash
export CEREBRAS_API_KEY="your-cerebras-key"
export GROQ_API_KEY="your-groq-key"
export OPENAI_API_KEY="your-openai-key"          # Optional
export ANTHROPIC_API_KEY="your-anthropic-key"    # Optional
```

The CLI uses sensible defaults for all other configuration:

- Default model: `cerebras/gpt-oss-120b`
- Default base URL: `http://localhost:4000`
- Default API key: `sk-balatrollm-proxy-key`
- Default strategy: `default`

### Usage

#### Quick Start

```bash
# 1. Start LiteLLM proxy (in separate terminal)
litellm --config config/litellm.yaml

# 2. Start Balatro with BalatroBot mod (in separate terminal)
./balatro.sh

# 3. Run the bot with default settings
balatrollm
```

#### `balatrollm` - Command Line Interface

```bash
balatrollm --help
```

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
  --model MODEL        Model name to use from LiteLLM proxy (default: cerebras/gpt-oss-120b)
  --list-models        List available models from the proxy and exit
  --strategy STRATEGY  Name of the strategy to use (default: default)
  --base-url BASE_URL  LiteLLM base URL (default: http://localhost:4000)
  --api-key API_KEY    LiteLLM proxy API key (default: sk-balatrollm-proxy- key)
  --config CONFIG      Load configuration from a previous run's config.json file
```

#### `Makefile` - Development Workflow

```bash
make help
```

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

#### `balatro.sh` - Game Automation

```bash
./balatro.sh --help
```

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

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Code style and conventions
- Testing guidelines
- Release process

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
