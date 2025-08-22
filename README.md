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

---

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
- Balatro instance with [BalatroBot](https://github.com/S1M0N38/balatrobot) running.

### Setup

```bash
# Clone the repository
git clone https://github.com/S1M0N38/balatrollm.git
cd balatrollm

# Create and activate environment
uv sync --all-extras

# Configure environment
cp .envrc.example .envrc

# Activate environment
source .envrc
```

### Usage

1. Start Balatro with BalatroBot

```bash
./balatro.sh
```

2. Start the LiteLLM proxy (in a separate terminal)

```bash
litellm --config config/litellm.yaml
```

3. Run the application

```bash
balatrollm
```

#### Alternative: Using the Makefile

For convenience, you can use the Makefile to automatically start both LiteLLM and Balatro:

```bash
make start
```

This will kill any previous instances and start both services automatically.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Code style and conventions
- Testing guidelines
- Release process

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  [Get Started](#quick-start) • [Contribute](CONTRIBUTING.md) • [Report Issues](https://github.com/S1M0N38/balatrollm/issues)
</div>
