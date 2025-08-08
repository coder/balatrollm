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

Add your project overview here.

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

1. Start the LiteLLM proxy (in a separate terminal)

```bash
litellm --config config/litellm.yaml
```

2. Run the application

```bash
balatrollm
```

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
